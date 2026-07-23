import dataclasses
import datetime
import logging
import xml.etree.ElementTree as ET
from types import TracebackType
from typing import Literal, Self, TypedDict
from xml.sax.saxutils import escape

import httpx
from django.conf import settings
from django.utils import timezone


logger = logging.getLogger(__name__)


IDENTITY_CALL_CONTENT = """\
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                  xmlns:impl="http://impl.ws.consultation.sngi.identification.isic.cnav/"
                  xmlns:giaw="http://www.GIAWBS01.Request.com">
  <soapenv:Header/>
  <soapenv:Body>
    <impl:identification>
      <arg0>
        <giaw:G-EnTeteMessage>
          <giaw:T-EmetteurMessage>
            <giaw:CdOrgNtl>{org_code}</giaw:CdOrgNtl>
            <giaw:LbOrgNtl>{org_label}</giaw:LbOrgNtl>
          </giaw:T-EmetteurMessage>
          <giaw:VersionWsdl>0300</giaw:VersionWsdl>
          <giaw:T-SouhaitsClient>
            <giaw:ChxRestLibCd>O</giaw:ChxRestLibCd>
            <giaw:ChxRestLibOrg>O</giaw:ChxRestLibOrg>
            <giaw:ChxRestInfSNGI>{requested_info}</giaw:ChxRestInfSNGI>
          </giaw:T-SouhaitsClient>
          <giaw:T-ContexteEchange>
            <giaw:App>SNGI</giaw:App>
            <giaw:Proc>TP</giaw:Proc>
            <giaw:TypMsg>411</giaw:TypMsg>
            <giaw:CdCor>0</giaw:CdCor>
          </giaw:T-ContexteEchange>
        </giaw:G-EnTeteMessage>
        <giaw:G-DonneesMetier>
          <giaw:G-OperationPersonne>
            <giaw:G-InfosPersonnePourIdent>
              <giaw:T-DdeIdentiteAssure>
                {request_data}
              </giaw:T-DdeIdentiteAssure>
            </giaw:G-InfosPersonnePourIdent>
          </giaw:G-OperationPersonne>
        </giaw:G-DonneesMetier>
      </arg0>
    </impl:identification>
  </soapenv:Body>
</soapenv:Envelope>"""


def identity_envelope(
    *,
    org_code: int,
    org_label: str,
    number: str,
    name: str,
    first_names: str | None = None,
    birth_date: datetime.date,
    sex_code: Literal[1, 2] | None = None,
    requested_info: str,
) -> str:
    request_data = [
        f"<giaw:NumAsrDemId>{escape(number)}</giaw:NumAsrDemId>",
        f"<giaw:NmAsrDemId>{escape(name)}</giaw:NmAsrDemId>",
        f"<giaw:DtNaiDem>{birth_date:%d%m%Y}</giaw:DtNaiDem>",
    ]
    if first_names:
        request_data.append(f"<giaw:LstPrnAsrDemId>{escape(first_names)}</giaw:LstPrnAsrDemId>")
    if sex_code:
        request_data.append(f"<giaw:CdSexDem>{escape(str(sex_code))}</giaw:CdSexDem>")

    return IDENTITY_CALL_CONTENT.format(
        org_code=str(org_code),
        org_label=org_label,
        requested_info=requested_info,
        request_data="\n".join(request_data),
    )


def prettify_xml_string(xml_str: str) -> str:
    xml = ET.fromstring(xml_str)
    ET.indent(xml)
    return ET.tostring(xml).decode()


@dataclasses.dataclass(frozen=True, slots=True)
class InterOpsExchange:
    request: str
    response: str
    response_status_code: int

    @property
    def pretty_request(self) -> str:
        return prettify_xml_string(self.request)

    @property
    def pretty_response(self) -> str:
        return prettify_xml_string(self.response)


class InterOpsClient:
    def __init__(
        self,
        base_url: str,
        org_code: int,
        org_label: str,
        subject_id: str,
        identity_path: str = "/PAC-AWSICONSL/AWSICONSL/QAL1/V1",
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.org_code = org_code
        self.org_label = org_label
        self.subject_id = subject_id
        self.identity_path = identity_path
        self.client = httpx.Client(
            base_url=self.base_url,
            headers={
                "Content-Type": "application/xml",
            },
        )

    def __enter__(self) -> Self:
        self.client.__enter__()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.client.__exit__(exc_type, exc_value, traceback)

    def interops_infos_header(self) -> dict[str, str]:
        return {
            "Interops-Infos": (
                "<InteropsInfos>"
                f"<LocalSubjectName>{self.subject_id}</LocalSubjectName>"
                f"<SubjectId>{self.subject_id}</SubjectId>"
                "<MethodAuthn>urn:oasis:names:tc:SAML:2.0:ac:classes:Password</MethodAuthn>"
                f"<AuthenticationDate>{timezone.now().strftime('%Y-%m-%dT%H:%M:%S.%fZ')}</AuthenticationDate>"
                "<Roles><Role>IDENT</Role></Roles>"
                "</InteropsInfos>"
            )
        }

    def _post(self, url: str, content: str) -> httpx.Response:
        return self.client.post(
            url,
            content=content,
            timeout=httpx.Timeout(5, read=60),
            headers=self.interops_infos_header(),
        ).raise_for_status()

    def identity(
        self,
        number: str,
        *,
        name: str,
        first_names: str | None = None,
        sex_code: Literal[1, 2] | None = None,
        birth_date: datetime.date,
    ) -> InterOpsExchange:
        content = identity_envelope(
            org_code=self.org_code,
            org_label=self.org_label,
            number=number,
            name=name,
            first_names=first_names,
            sex_code=sex_code,
            birth_date=birth_date,
            # 0: Not all infos
            # 1: Person identity
            # 0: No family info
            # 1: Specific information (like common & marital name)
            # 0: No neighbour info
            # 0: Unused
            # 1: Decease information
            # 1: Identification number history
            requested_info="010100110000000",
        )
        response = self._post(url=self.identity_path, content=content)
        return InterOpsExchange(request=content, response=response.text, response_status_code=response.status_code)


class InterOpsParseException(Exception):
    pass


NS = {
    "soap": "http://schemas.xmlsoap.org/soap/envelope/",
    "impl": "http://impl.ws.consultation.sngi.identification.isic.cnav/",
    "giawbs": "http://www.GIAWBS01.Response.com",
}


def convert_sngi_date_to_iso(date_str: str) -> str:
    if len(date_str) != 8:
        raise ValueError(f"Invalid date string: {date_str}")
    return f"{date_str[4:]}-{date_str[2:4]}-{date_str[:2]}"


def sanitize_sex_code(sex_code: str | None) -> Literal[1, 2] | None:
    if sex_code is None:
        return None
    try:
        sex_int = int(sex_code)
        if sex_int not in (1, 2):
            raise ValueError
    except ValueError:
        logger.warning(f"Invalid sex_code: {sex_code}")
        return None
    return sex_int


def et_get_mandatory_node_text(parent: ET.Element, path: str) -> str | None:
    node = parent.find(path, NS)
    if node is None:
        logger.warning(f"Missing {path} node.")
        return None
    if node.text is None:
        logger.warning(f"Missing {path} content.")
        return None
    return node.text


def death_date(sngi_result: ET.Element) -> str | None:
    # The date of death might contain unknown day/month/year
    # Return a string to avoid invalid dates
    decease_node = sngi_result.find("./giawbs:T-ResDeces", NS)
    if decease_node is None:
        return None
    certification_code = decease_node.find("./giawbs:CdCertDcRes", NS)
    # If a certification code of 7 or 8 is provided, it means that the decease has been cancelled
    if certification_code is not None and certification_code.text in ("7", "8"):
        return None
    death_date_node_text = et_get_mandatory_node_text(decease_node, "./giawbs:DtDcRes")
    return convert_sngi_date_to_iso(death_date_node_text) if death_date_node_text is not None else None


def et_find_one(parent: ET.Element, path: str) -> ET.Element:
    try:
        [node] = parent.findall(path, NS)
    except ValueError as exc:
        raise InterOpsParseException(f"Expected a single {path} node") from exc
    return node


def extract_identity_infos(sngi_result: ET.Element) -> dict[str, str | None]:
    infos_node = et_find_one(sngi_result, "./giawbs:T-ResIdentiteAssure")
    matching = {
        f"{{{NS['giawbs']}}}NumAsrRes": "number",
        f"{{{NS['giawbs']}}}NmAsrAccRes": "accented_name",
        f"{{{NS['giawbs']}}}NmAsrFltrRes": "filtered_name",
        f"{{{NS['giawbs']}}}LstPrnAsrAccRes": "accented_firstnames",
        f"{{{NS['giawbs']}}}LstPrnAsrFltrRes": "filtered_firstnames",
        f"{{{NS['giawbs']}}}CdSexRes": "sex_code",
        f"{{{NS['giawbs']}}}DtNaiRes": "birth_date",
        f"{{{NS['giawbs']}}}CdLieNaiRes": "birth_place",
    }
    infos = {}
    for child_node in infos_node:
        target_field_name = matching.get(child_node.tag)
        if target_field_name is not None:
            infos[target_field_name] = child_node.text
    return infos


def number_history(sngi_result: ET.Element) -> list[str]:
    numbers = []
    for history in sngi_result.findall("./giawbs:T-ResHistoIdentifiantAss", NS):
        number_node_text = et_get_mandatory_node_text(history, "./giawbs:NumAsrRecRes")
        if number_node_text is not None:
            numbers.append(number_node_text)
    return numbers


class OtherNames(TypedDict):
    common_name: Name | None
    marital_name: Name | None


def get_other_names(sngi_result: ET.Element) -> OtherNames:
    common_name_infos = []
    marital_name_infos = []

    def _get_name_date(date_node: ET.Element | None) -> datetime.date:
        if date_node is not None and date_node.text:
            return datetime.date.strptime(date_node.text, "%d%m%Y")
        return datetime.date(1, 1, 1)  # Use an old date to prefer names with a date

    for node_index, history in enumerate(sngi_result.findall("giawbs:T-ResInfosSpecifiquesOrganisme", NS)):
        filtered_marital_node = history.find("./giawbs:ISONmMarlFltrRes", NS)
        if filtered_marital_node is not None and (filtered_marital_name := filtered_marital_node.text):
            marital_date = _get_name_date(history.find("./giawbs:ISODtoMarRes", NS))
            accented_marital_node = history.find("./giawbs:ISONmMarlAccRes", NS)
            accented_marital_name = accented_marital_node.text if accented_marital_node is not None else None
            marital_name_infos.append(
                (
                    marital_date,
                    node_index,
                    Name.from_names(accented=accented_marital_name, filtered=filtered_marital_name),
                )
            )

        filtered_common_node = history.find("./giawbs:ISONmUsgFltrRes", NS)
        if filtered_common_node is not None and (filtered_common_name := filtered_common_node.text):
            common_date = _get_name_date(history.find("./giawbs:ISODtoUsgRes", NS))
            accented_common_node = history.find("./giawbs:ISONmUsgAccRes", NS)
            accented_common_name = accented_common_node.text if accented_common_node is not None else None
            common_name_infos.append(
                (
                    common_date,
                    node_index,
                    Name.from_names(accented=accented_common_name, filtered=filtered_common_name),
                )
            )

    # Prefer names with recent date or the last one in the XML
    return {
        "common_name": max(common_name_infos)[2] if common_name_infos else None,
        "marital_name": max(marital_name_infos)[2] if marital_name_infos else None,
    }


@dataclasses.dataclass(frozen=True, slots=True)
class Name:
    accented: str | None
    filtered: str | None

    @classmethod
    def from_names(cls, accented: str | None, filtered: str | None) -> Self | None:
        if not accented and not filtered:
            return None
        return cls(accented=accented, filtered=filtered)


@dataclasses.dataclass(frozen=True, slots=True)
class FirstNames:
    accented: list[str]
    filtered: list[str]

    @classmethod
    def from_first_names(cls, accented: str | None, filtered: str | None) -> Self | None:
        if not accented and not filtered:
            return None
        return cls(
            accented=accented.split() if accented else [],
            filtered=filtered.split() if filtered else [],
        )


@dataclasses.dataclass(frozen=True, slots=True)
class PersonalInfos:
    number: str
    sex_code: Literal[1] | Literal[2] | None
    birth_date: str | None
    birth_place: str | None
    death_date: str | None
    number_history: list[str]

    birth_name: Name | None
    common_name: Name | None
    marital_name: Name | None

    first_names: FirstNames | None


@dataclasses.dataclass(frozen=True, slots=True)
class InterOpsResult:
    code: int
    label: str | None

    infos: PersonalInfos | None = None


def parse_response(response_text: str) -> InterOpsResult:
    try:
        xml = ET.fromstring(response_text)
    except ET.ParseError as exc:
        raise InterOpsParseException("Invalid XML") from exc
    if xml.tag != "{http://schemas.xmlsoap.org/soap/envelope/}Envelope":
        raise InterOpsParseException(f"Unexpected XML with root tag: {xml.tag}")
    return_node = et_find_one(xml, "./soap:Body/impl:identificationResponse/return")
    global_result = et_find_one(return_node, "./giawbs:T-ResultatGlobal")
    result_code = et_find_one(global_result, "./giawbs:CdResTrtInfoGlo")
    result_label = et_find_one(global_result, "./giawbs:LibResTrtInfoGlo")

    try:
        if result_code.text is None:
            raise ValueError
        result_code = int(result_code.text)
    except ValueError:
        raise InterOpsParseException(
            f"Invalid {{{NS['giawbs']}}}:CdResTrtInfoGlo content: {result_code.text}"
        ) from None

    if result_code not in (1000, 5000):
        return InterOpsResult(code=result_code, label=result_label.text)
    sngi_result = et_find_one(
        return_node, "./giawbs:G-DonneesMetierRes/giawbs:G-ResultatDonnees/giawbs:G-ResultatSNGI"
    )
    infos = extract_identity_infos(sngi_result)
    number = infos.get("number")
    if not number:
        raise InterOpsParseException(f"Missing mandatory {{{NS['giawbs']}}}:NumAsrRes node or content")
    if (birth_date_str := infos.get("birth_date")) is not None:
        birth_date = convert_sngi_date_to_iso(birth_date_str)
    else:
        birth_date = None
    other_names = get_other_names(sngi_result)

    return InterOpsResult(
        code=result_code,
        label=result_label.text,
        infos=PersonalInfos(
            number=number,
            sex_code=sanitize_sex_code(infos.get("sex_code")),
            birth_name=Name.from_names(accented=infos.get("accented_name"), filtered=infos.get("filtered_name")),
            common_name=other_names["common_name"],
            marital_name=other_names["marital_name"],
            first_names=FirstNames.from_first_names(
                accented=infos.get("accented_firstnames"), filtered=infos.get("filtered_firstnames")
            ),
            birth_date=birth_date,
            birth_place=infos.get("birth_place"),
            death_date=death_date(sngi_result),
            number_history=number_history(sngi_result),
        ),
    )


def get_client() -> InterOpsClient:
    return InterOpsClient(
        base_url=settings.INTEROPS_BASE_URL,
        org_code=settings.INTEROPS_ORGANIZATION_CODE,
        org_label=settings.INTEROPS_ORGANIZATION_LABEL,
        subject_id=settings.INTEROPS_SUBJECT_ID,
        identity_path=settings.INTEROPS_IDENTITY_PATH,
    )
