import datetime
import xml.etree.ElementTree as ET

import pytest
import respx
from freezegun import freeze_time

from api_relay_cnav.utils.interops import (
    FirstNames,
    InterOpsClient,
    InterOpsParseException,
    InterOpsResult,
    Name,
    PersonalInfos,
    death_date,
    get_client,
    get_other_names,
    number_history,
    parse_response,
)


@respx.mock
@freeze_time("2026-06-30 12:01:02.34")
def test_client(snapshot):
    interops_route = respx.post("http://interops/PAC-AWSICONSL/AWSICONSL/QAL1/V1").respond(200, content="This is XML")

    client = InterOpsClient(
        base_url="http://interops",
        org_code="1234",
        org_label="Notre organisation",
        subject_id="urn::subject::id",
    )

    exchange = client.identity(
        number="1234567890123",
        name="Martin",
        first_names="Jean Paul François",
        sex_code="1",
        birth_date=datetime.date(1990, 1, 1),
    )
    [interops_call] = interops_route.calls
    assert interops_call.request.headers["interops-infos"] == (
        "<InteropsInfos>"
        "<LocalSubjectName>urn::subject::id</LocalSubjectName>"
        "<SubjectId>urn::subject::id</SubjectId>"
        "<MethodAuthn>urn:oasis:names:tc:SAML:2.0:ac:classes:Password</MethodAuthn>"
        "<AuthenticationDate>2026-06-30T12:01:02.340000Z</AuthenticationDate>"
        "<Roles><Role>IDENT</Role></Roles>"
        "</InteropsInfos>"
    )
    assert interops_call.request.content.decode() == exchange.request
    assert exchange.request == snapshot(name="request content")
    assert exchange.response == "This is XML"


class TestInteropsParsing:
    def test_invalid_responses(self):
        with pytest.raises(InterOpsParseException, match="Invalid XML"):
            parse_response("WAT")
        with pytest.raises(InterOpsParseException, match="Unexpected XML with "):
            parse_response("<enveloppe/>")
        with pytest.raises(
            InterOpsParseException, match="Expected a single ./soap:Body/impl:identificationResponse/return node"
        ):
            parse_response(
                '<ns0:Envelope xmlns:ns0="http://schemas.xmlsoap.org/soap/envelope/">'
                "<ns0:Body>summer</ns0:Body>"
                "</ns0:Envelope>"
            )
        with pytest.raises(InterOpsParseException, match="Expected a single ./giawbs:T-ResultatGlobal node"):
            parse_response("""\
                <ns0:Envelope xmlns:ns0="http://schemas.xmlsoap.org/soap/envelope/"
                              xmlns:ns1="http://impl.ws.consultation.sngi.identification.isic.cnav/" >
                  <ns0:Body>
                    <ns1:identificationResponse>
                      <return>
                      </return>
                    </ns1:identificationResponse>
                  </ns0:Body>
                </ns0:Envelope>""")
        with pytest.raises(
            InterOpsParseException, match="Invalid {http://www.GIAWBS01.Response.com}:CdResTrtInfoGlo content: wazaaaa"
        ):
            parse_response("""\
                <ns0:Envelope xmlns:ns0="http://schemas.xmlsoap.org/soap/envelope/"
                              xmlns:ns1="http://impl.ws.consultation.sngi.identification.isic.cnav/"
                              xmlns:ns2="http://www.GIAWBS01.Response.com" >
                  <ns0:Body>
                    <ns1:identificationResponse>
                      <return>
                        <ns2:T-ResultatGlobal>
                          <ns2:CdResTrtInfoGlo>wazaaaa</ns2:CdResTrtInfoGlo>
                          <ns2:LibResTrtInfoGlo>R&#233;sultat OK</ns2:LibResTrtInfoGlo>
                          <ns2:DtTrtRes>260706173613</ns2:DtTrtRes>
                          <ns2:CodImmatriculable>1</ns2:CodImmatriculable>
                        </ns2:T-ResultatGlobal>
                      </return>
                    </ns1:identificationResponse>
                  </ns0:Body>
                </ns0:Envelope>""")

    def wrap_sngi_result(self, sngi_result):
        return f"""\
            <ns0:Envelope xmlns:ns0="http://schemas.xmlsoap.org/soap/envelope/"
                          xmlns:ns1="http://impl.ws.consultation.sngi.identification.isic.cnav/"
                          xmlns:ns2="http://www.GIAWBS01.Response.com"
                          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
              <ns0:Body>
                <ns1:identificationResponse>
                  <return>
                    <ns2:G-EnTeteMessage>
                      <ns2:T-EmetteurMessage>
                        <ns2:CdOrgNtl>18</ns2:CdOrgNtl>
                        <ns2:LbOrgNtl>CNAV OPERATEUR</ns2:LbOrgNtl>
                        <ns2:CdOrgGst xsi:nil="true" />
                        <ns2:LbOrgGst xsi:nil="true" />
                        <ns2:CdDmn xsi:nil="true" />
                        <ns2:LbDmn xsi:nil="true" />
                        <ns2:CdSi>18</ns2:CdSi>
                        <ns2:LbSi>CNAV OPERATEUR</ns2:LbSi>
                      </ns2:T-EmetteurMessage>
                      <ns2:VersionWsdl>300</ns2:VersionWsdl>
                      <ns2:T-SouhaitsClient>
                        <ns2:ZnCliEch xsi:nil="true" />
                        <ns2:ChxRestLibCd>O</ns2:ChxRestLibCd>
                        <ns2:ChxRestLibOrg>O</ns2:ChxRestLibOrg>
                        <ns2:ChxRestInfSNGI>010100110000000</ns2:ChxRestInfSNGI>
                      </ns2:T-SouhaitsClient>
                      <ns2:T-ContexteEchange>
                        <ns2:App>SNGI</ns2:App>
                        <ns2:Proc>RESULTAT CONSULTATION</ns2:Proc>
                        <ns2:TypMsg>411</ns2:TypMsg>
                        <ns2:CdCor xsi:nil="true" />
                      </ns2:T-ContexteEchange>
                    </ns2:G-EnTeteMessage>
                    <ns2:T-ResultatGlobal>
                      <ns2:CdResTrtInfoGlo>1000</ns2:CdResTrtInfoGlo>
                      <ns2:LibResTrtInfoGlo>R&#233;sultat OK</ns2:LibResTrtInfoGlo>
                      <ns2:DtTrtRes>260706173613</ns2:DtTrtRes>
                      <ns2:CodImmatriculable>1</ns2:CodImmatriculable>
                    </ns2:T-ResultatGlobal>
                    <ns2:G-DonneesMetierRes>
                      <ns2:G-ResultatDonnees>
                        <ns2:G-ResultatSNGI>
                          {sngi_result}
                        </ns2:G-ResultatSNGI>
                      </ns2:G-ResultatDonnees>
                    </ns2:G-DonneesMetierRes>
                  </return>
                </ns1:identificationResponse>
              </ns0:Body>
            </ns0:Envelope>"""

    def test_error_responses(self):
        infos = parse_response("""\
            <ns0:Envelope xmlns:ns0="http://schemas.xmlsoap.org/soap/envelope/"
                          xmlns:ns1="http://impl.ws.consultation.sngi.identification.isic.cnav/"
                          xmlns:ns2="http://www.GIAWBS01.Response.com"
                          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
              <ns0:Body>
                <ns1:identificationResponse>
                  <return>
                    <ns2:T-ResultatGlobal>
                      <ns2:CdResTrtInfoGlo>9000</ns2:CdResTrtInfoGlo>
                      <ns2:LibResTrtInfoGlo>KO Fonctionnel</ns2:LibResTrtInfoGlo>
                      <ns2:DtTrtRes>260706173613</ns2:DtTrtRes>
                      <ns2:CodImmatriculable>1</ns2:CodImmatriculable>
                    </ns2:T-ResultatGlobal>
                    <ns2:G-DonneesMetierRes>
                      <ns2:G-ResultatBlocDemande>
                        <ns2:T-ResultatTraitInfosWS>
                          <ns2:TypBlk>IDENT</ns2:TypBlk>
                          <ns2:CdResTrtInfo>9000</ns2:CdResTrtInfo>
                          <ns2:LibResTrtInfo>KO Fonctionnel</ns2:LibResTrtInfo>
                        </ns2:T-ResultatTraitInfosWS>
                        <ns2:T-ErreurSignalement>
                          <ns2:CdErrSgn>9013</ns2:CdErrSgn>
                          <ns2:LibErrSgn>Ident : NIR non trouv&#233; dans la base SNGI</ns2:LibErrSgn>
                          <ns2:LibErrSgnCourt xsi:nil="true" />
                        </ns2:T-ErreurSignalement>
                      </ns2:G-ResultatBlocDemande>
                    </ns2:G-DonneesMetierRes>
                  </return>
                </ns1:identificationResponse>
              </ns0:Body>
            </ns0:Envelope>""")
        assert infos == InterOpsResult(code=9000, label="KO Fonctionnel")

    def test_simple_response(self):
        infos = parse_response(
            self.wrap_sngi_result("""\
                <ns2:T-ResIdentiteAssure>
                  <ns2:NumAsrRes>1540629232963</ns2:NumAsrRes>
                  <ns2:NmAsrFltrRes>MILLET</ns2:NmAsrFltrRes>
                  <ns2:LstPrnAsrFltrRes>EMMANUEL EMILE PIERRE</ns2:LstPrnAsrFltrRes>
                  <ns2:NmAsrAccRes>MILLET</ns2:NmAsrAccRes>
                  <ns2:LstPrnAsrAccRes>Emmanuel Emile Pierre</ns2:LstPrnAsrAccRes>
                  <ns2:CdSexRes>1</ns2:CdSexRes>
                  <ns2:LibCdSexRes>Masculin</ns2:LibCdSexRes>
                  <ns2:DtNaiRes>27061954</ns2:DtNaiRes>
                  <ns2:CdLieNaiRes>29232</ns2:CdLieNaiRes>
                  <ns2:LibDepNaiRes>FINISTERE</ns2:LibDepNaiRes>
                  <ns2:LibCmnNaiRes>QUIMPER</ns2:LibCmnNaiRes>
                  <ns2:LibPayNaiRes xsi:nil="true" />
                  <ns2:LibLocNaiRes xsi:nil="true" />
                  <ns2:CdCertEclRes>3</ns2:CdCertEclRes>
                  <ns2:LibCdCertEclRes>Reconnu par l'INSEE</ns2:LibCdCertEclRes>
                  <ns2:DtoEclRes>25112024</ns2:DtoEclRes>
                  <ns2:CodMnlPayNaiRes>F</ns2:CodMnlPayNaiRes>
                  <ns2:LibMnlPayNaiRes>FRANCE</ns2:LibMnlPayNaiRes>
                  <ns2:CodPceEclRes xsi:nil="true" />
                  <ns2:LibPceEclRes xsi:nil="true" />
                  <ns2:DtCertif />
                </ns2:T-ResIdentiteAssure>
                """)
        )
        assert infos == InterOpsResult(
            code=1000,
            label="Résultat OK",
            infos=PersonalInfos(
                birth_date="1954-06-27",
                birth_place="29232",
                common_name=None,
                death_date=None,
                first_names=FirstNames(
                    accented=["Emmanuel", "Emile", "Pierre"], filtered=["EMMANUEL", "EMILE", "PIERRE"]
                ),
                marital_name=None,
                birth_name=Name(accented="MILLET", filtered="MILLET"),
                number="1540629232963",
                number_history=[],
                sex_code=1,
            ),
        )

    def test_missing_number(self):
        with pytest.raises(
            InterOpsParseException,
            match="Missing mandatory {http://www.GIAWBS01.Response.com}:NumAsrRes node or content",
        ):
            parse_response(
                self.wrap_sngi_result("""\
                    <ns2:T-ResIdentiteAssure>
                      <ns2:NmAsrFltrRes>MILLET</ns2:NmAsrFltrRes>
                      <ns2:LstPrnAsrFltrRes>EMMANUEL EMILE PIERRE</ns2:LstPrnAsrFltrRes>
                      <ns2:NmAsrAccRes>MILLET</ns2:NmAsrAccRes>
                      <ns2:LstPrnAsrAccRes>Emmanuel Emile Pierre</ns2:LstPrnAsrAccRes>
                      <ns2:CdSexRes>1</ns2:CdSexRes>
                      <ns2:LibCdSexRes>Masculin</ns2:LibCdSexRes>
                      <ns2:DtNaiRes>27061954</ns2:DtNaiRes>
                      <ns2:CdLieNaiRes>29232</ns2:CdLieNaiRes>
                      <ns2:LibDepNaiRes>FINISTERE</ns2:LibDepNaiRes>
                      <ns2:LibCmnNaiRes>QUIMPER</ns2:LibCmnNaiRes>
                      <ns2:LibPayNaiRes xsi:nil="true" />
                      <ns2:LibLocNaiRes xsi:nil="true" />
                      <ns2:CdCertEclRes>3</ns2:CdCertEclRes>
                      <ns2:LibCdCertEclRes>Reconnu par l'INSEE</ns2:LibCdCertEclRes>
                      <ns2:DtoEclRes>25112024</ns2:DtoEclRes>
                      <ns2:CodMnlPayNaiRes>F</ns2:CodMnlPayNaiRes>
                      <ns2:LibMnlPayNaiRes>FRANCE</ns2:LibMnlPayNaiRes>
                      <ns2:CodPceEclRes xsi:nil="true" />
                      <ns2:LibPceEclRes xsi:nil="true" />
                      <ns2:DtCertif />
                    </ns2:T-ResIdentiteAssure>
                    """)
            )

    def test_complete_response(self):
        infos = parse_response(
            self.wrap_sngi_result("""\
              <ns2:T-ResIdentiteAssure>
                <ns2:NumAsrRes>1540629232963</ns2:NumAsrRes>
                <ns2:NmAsrFltrRes>MILLET</ns2:NmAsrFltrRes>
                <ns2:LstPrnAsrFltrRes>EMMANUEL EMILE PIERRE</ns2:LstPrnAsrFltrRes>
                <ns2:NmAsrAccRes>MILLET</ns2:NmAsrAccRes>
                <ns2:LstPrnAsrAccRes>Emmanuel Emile Pierre</ns2:LstPrnAsrAccRes>
                <ns2:CdSexRes>1</ns2:CdSexRes>
                <ns2:LibCdSexRes>Masculin</ns2:LibCdSexRes>
                <ns2:DtNaiRes>27061954</ns2:DtNaiRes>
                <ns2:CdLieNaiRes>29232</ns2:CdLieNaiRes>
                <ns2:LibDepNaiRes>FINISTERE</ns2:LibDepNaiRes>
                <ns2:LibCmnNaiRes>QUIMPER</ns2:LibCmnNaiRes>
                <ns2:LibPayNaiRes xsi:nil="true" />
                <ns2:LibLocNaiRes xsi:nil="true" />
                <ns2:CdCertEclRes>3</ns2:CdCertEclRes>
                <ns2:LibCdCertEclRes>Reconnu par l'INSEE</ns2:LibCdCertEclRes>
                <ns2:DtoEclRes>25112024</ns2:DtoEclRes>
                <ns2:CodMnlPayNaiRes>F</ns2:CodMnlPayNaiRes>
                <ns2:LibMnlPayNaiRes>FRANCE</ns2:LibMnlPayNaiRes>
                <ns2:CodPceEclRes xsi:nil="true" />
                <ns2:LibPceEclRes xsi:nil="true" />
                <ns2:DtCertif />
              </ns2:T-ResIdentiteAssure>
              <ns2:T-ResInfosSpecifiquesOrganisme>
                <ns2:ISONmMarlFltrRes xsi:nil="true" />
                <ns2:ISONmMarlAccRes xsi:nil="true" />
                <ns2:ISODtoMarRes xsi:nil="true" />
                <ns2:ISONmUsgFltrRes>DUVAL</ns2:ISONmUsgFltrRes>
                <ns2:ISONmUsgAccRes xsi:nil="true" />
                <ns2:ISOPrnUsgFltrRes xsi:nil="true" />
                <ns2:ISOPrnUsgAccRes xsi:nil="true" />
                <ns2:ISODtoUsgRes xsi:nil="true" />
                <ns2:ISONumItnOrgRes xsi:nil="true" />
                <ns2:ISODtoPrnUsgRes />
                <ns2:ISODtoNumItnOrgRes />
                <ns2:ISODtoAbonRes />
              </ns2:T-ResInfosSpecifiquesOrganisme>
              <ns2:T-ResDeces>
                <ns2:DtDcRes>10032022</ns2:DtDcRes>
                <ns2:DtoDcRes>25112024</ns2:DtoDcRes>
                <ns2:NumActeDcRes xsi:nil="true" />
                <ns2:CdOrgOriDcRes>19</ns2:CdOrgOriDcRes>
                <ns2:LibOrgOriDcRes>INSEE</ns2:LibOrgOriDcRes>
                <ns2:CdCertDcRes>3</ns2:CdCertDcRes>
                <ns2:LibCdCertDcRes>Certifi&#233; INSEE d&#233;c&#232;s normal</ns2:LibCdCertDcRes>
                <ns2:CdPieDcRes xsi:nil="true" />
                <ns2:LibPieDcRes xsi:nil="true" />
                <ns2:CdLieDcRes xsi:nil="true" />
                <ns2:LibDepDcRes xsi:nil="true" />
                <ns2:LibCmnDcRes xsi:nil="true" />
                <ns2:LibPayDcRes xsi:nil="true" />
                <ns2:LibLocDcRes xsi:nil="true" />
                <ns2:CdMnlPayDceRes xsi:nil="true" />
                <ns2:LibMnlPayDceRes xsi:nil="true" />
              </ns2:T-ResDeces>
              <ns2:T-ResHistoIdentifiantAss>
                <ns2:NumAsrRecRes>1540629232963</ns2:NumAsrRecRes>
                <ns2:DtoNumAsrRecRes>25112024</ns2:DtoNumAsrRecRes>
                <ns2:SieNaisPrec xsi:nil="true" />
                <ns2:CdCertEclNaisPrec xsi:nil="true" />
                <ns2:LibCdCertEclNaisPrec xsi:nil="true" />
                <ns2:CodMtfModNir xsi:nil="true" />
              </ns2:T-ResHistoIdentifiantAss>
                """)
        )
        assert infos == InterOpsResult(
            code=1000,
            label="Résultat OK",
            infos=PersonalInfos(
                birth_date="1954-06-27",
                birth_place="29232",
                common_name=Name(accented=None, filtered="DUVAL"),
                death_date="2022-03-10",
                first_names=FirstNames(
                    accented=["Emmanuel", "Emile", "Pierre"], filtered=["EMMANUEL", "EMILE", "PIERRE"]
                ),
                marital_name=None,
                birth_name=Name(accented="MILLET", filtered="MILLET"),
                number="1540629232963",
                number_history=["1540629232963"],
                sex_code=1,
            ),
        )


class TestDeathDateParsing:
    def test_no_death(self):
        assert (
            death_date(
                ET.fromstring("""\
                <ns2:G-ResultatSNGI xmlns:ns2="http://www.GIAWBS01.Response.com">
                </ns2:G-ResultatSNGI>""")
            )
            is None
        )

    def test_nominal_death(self):
        assert (
            death_date(
                ET.fromstring("""\
                <ns2:G-ResultatSNGI xmlns:ns2="http://www.GIAWBS01.Response.com">
                  <ns2:T-ResDeces>
                    <ns2:DtDcRes>10032022</ns2:DtDcRes>
                    <ns2:DtoDcRes>25112024</ns2:DtoDcRes>
                    <ns2:CdCertDcRes>3</ns2:CdCertDcRes>
                  </ns2:T-ResDeces>
                </ns2:G-ResultatSNGI>""")
            )
            == "2022-03-10"
        )

    @pytest.mark.parametrize(("certification_code", "expected_value"), [(2, "2022-03-10"), (7, None), (8, None)])
    def test_cancelled_death(self, certification_code, expected_value):
        assert (
            death_date(
                ET.fromstring(f"""\
                <ns2:G-ResultatSNGI xmlns:ns2="http://www.GIAWBS01.Response.com">
                  <ns2:T-ResDeces>
                    <ns2:DtDcRes>10032022</ns2:DtDcRes>
                    <ns2:DtoDcRes>25112024</ns2:DtoDcRes>
                    <ns2:CdCertDcRes>{certification_code}</ns2:CdCertDcRes>
                  </ns2:T-ResDeces>
                </ns2:G-ResultatSNGI>""")
            )
            == expected_value
        )

    @pytest.mark.parametrize(
        ("sngi_date", "expected_value"),
        [
            ("10032022", "2022-03-10"),
            ("00032022", "2022-03-00"),
            ("00002022", "2022-00-00"),
            ("00000000", "0000-00-00"),
        ],
    )
    def test_approximate_death(self, sngi_date, expected_value):
        assert (
            death_date(
                ET.fromstring(f"""\
                <ns2:G-ResultatSNGI xmlns:ns2="http://www.GIAWBS01.Response.com">
                  <ns2:T-ResDeces>
                    <ns2:DtDcRes>{sngi_date}</ns2:DtDcRes>
                    <ns2:DtoDcRes>25112024</ns2:DtoDcRes>
                    <ns2:CdCertDcRes>3</ns2:CdCertDcRes>
                  </ns2:T-ResDeces>
                </ns2:G-ResultatSNGI>""")
            )
            == expected_value
        )


class TestNumberHistory:
    def test_no_history(self):
        assert (
            number_history(
                ET.fromstring("""\
                <ns2:G-ResultatSNGI xmlns:ns2="http://www.GIAWBS01.Response.com">
                </ns2:G-ResultatSNGI>""")
            )
            == []
        )

    def test_several_numbers(self):
        assert number_history(
            ET.fromstring("""\
                <ns2:G-ResultatSNGI xmlns:ns2="http://www.GIAWBS01.Response.com">
                  <ns2:T-ResHistoIdentifiantAss>
                    <ns2:NumAsrRecRes>1234567890123</ns2:NumAsrRecRes>
                  </ns2:T-ResHistoIdentifiantAss>
                  <ns2:T-ResHistoIdentifiantAss>
                    <ns2:NumAsrRecRes>1234567890124</ns2:NumAsrRecRes>
                  </ns2:T-ResHistoIdentifiantAss>
                  <ns2:T-ResHistoIdentifiantAss>
                    <ns2:NumAsrRecRes>1234567890125</ns2:NumAsrRecRes>
                  </ns2:T-ResHistoIdentifiantAss>
                </ns2:G-ResultatSNGI>""")
        ) == [
            "1234567890123",
            "1234567890124",
            "1234567890125",
        ]


class TestGetOtherNames:
    def test_no_history(self):
        assert get_other_names(
            ET.fromstring("""\
                <ns2:G-ResultatSNGI xmlns:ns2="http://www.GIAWBS01.Response.com">
                </ns2:G-ResultatSNGI>""")
        ) == {"common_name": None, "marital_name": None}

    def test_both(self):
        assert get_other_names(
            ET.fromstring("""\
                <ns2:G-ResultatSNGI xmlns:ns2="http://www.GIAWBS01.Response.com"
                                    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                  <ns2:T-ResInfosSpecifiquesOrganisme>
                    <ns2:ISONmMarlFltrRes>MARIE</ns2:ISONmMarlFltrRes>
                    <ns2:ISONmMarlAccRes xsi:nil="true" />
                    <ns2:ISODtoMarRes xsi:nil="true" />
                    <ns2:ISONmUsgFltrRes>DUVAL</ns2:ISONmUsgFltrRes>
                    <ns2:ISONmUsgAccRes xsi:nil="true" />
                    <ns2:ISODtoUsgRes xsi:nil="true" />
                  </ns2:T-ResInfosSpecifiquesOrganisme>
                </ns2:G-ResultatSNGI>""")
        ) == {
            "common_name": Name(accented=None, filtered="DUVAL"),
            "marital_name": Name(accented=None, filtered="MARIE"),
        }

    def test_prefer_recent_names(self):
        assert get_other_names(
            ET.fromstring("""\
                <ns2:G-ResultatSNGI xmlns:ns2="http://www.GIAWBS01.Response.com"
                                    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                  <ns2:T-ResInfosSpecifiquesOrganisme>
                    <ns2:ISONmMarlFltrRes>MARIE</ns2:ISONmMarlFltrRes>
                    <ns2:ISONmMarlAccRes xsi:nil="true" />
                    <ns2:ISODtoMarRes>31012022</ns2:ISODtoMarRes>
                    <ns2:ISONmUsgFltrRes>DUVAL</ns2:ISONmUsgFltrRes>
                    <ns2:ISONmUsgAccRes xsi:nil="true" />
                    <ns2:ISODtoUsgRes>31012022</ns2:ISODtoUsgRes>
                  </ns2:T-ResInfosSpecifiquesOrganisme>
                  <ns2:T-ResInfosSpecifiquesOrganisme>
                    <ns2:ISONmMarlFltrRes>MARY</ns2:ISONmMarlFltrRes>
                    <ns2:ISONmMarlAccRes xsi:nil="true" />
                    <ns2:ISODtoMarRes>31012023</ns2:ISODtoMarRes>
                    <ns2:ISONmUsgFltrRes>BUVAL</ns2:ISONmUsgFltrRes>
                    <ns2:ISONmUsgAccRes xsi:nil="true" />
                    <ns2:ISODtoUsgRes>31012021</ns2:ISODtoUsgRes>
                  </ns2:T-ResInfosSpecifiquesOrganisme>
                  <ns2:T-ResInfosSpecifiquesOrganisme>
                    <ns2:ISONmMarlFltrRes>MARI</ns2:ISONmMarlFltrRes>
                    <ns2:ISONmMarlAccRes xsi:nil="true" />
                    <ns2:ISODtoMarRes xsi:nil="true" />
                    <ns2:ISONmUsgFltrRes>DUCAL</ns2:ISONmUsgFltrRes>
                    <ns2:ISONmUsgAccRes xsi:nil="true" />
                    <ns2:ISODtoUsgRes xsi:nil="true" />
                  </ns2:T-ResInfosSpecifiquesOrganisme>
                </ns2:G-ResultatSNGI>""")
        ) == {
            "common_name": Name(accented=None, filtered="DUVAL"),
            "marital_name": Name(accented=None, filtered="MARY"),
        }


def test_get_client(settings):
    settings.INTEROPS_BASE_URL = "http://base.url"
    settings.INTEROPS_ORGANIZATION_CODE = 4321
    settings.INTEROPS_ORGANIZATION_LABEL = "Label de 4321"
    settings.INTEROPS_SUBJECT_ID = "urn"
    settings.INTEROPS_IDENTITY_PATH = "/path/to/identity/"

    client = get_client()
    assert client.base_url == "http://base.url"
    assert client.org_code == 4321
    assert client.org_label == "Label de 4321"
    assert client.subject_id == "urn"
    assert client.identity_path == "/path/to/identity/"
