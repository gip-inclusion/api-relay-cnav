import datetime
import random
import uuid

import factory
import factory.fuzzy


def generate_number(*, birth_date, sex_code=None, birth_place=None):
    if sex_code is None:
        sex_code = random.randint(1, 2)
    if birth_place is None:
        department = str(random.randint(1, 99)).zfill(2)
        random_1 = str(random.randint(0, 399)).zfill(3)
        birth_place = f"{department}{random_1}"
    else:
        assert len(birth_place) == 5
    gender = random.choice("137" if sex_code == 1 else "248")
    year_month = birth_date.strftime("%y%m")
    random_2 = str(random.randint(0, 399)).zfill(3)
    return f"{gender}{year_month}{birth_place}{random_2}"


class IdentityRequestFactory(factory.DictFactory):
    request_uid = factory.LazyFunction(uuid.uuid4)
    name = factory.Faker("last_name")
    first_names = factory.Faker("first_name")
    birth_date = factory.fuzzy.FuzzyDate(datetime.date(1968, 1, 1), datetime.date(1999, 12, 31))

    @factory.lazy_attribute
    def number(self):
        return generate_number(birth_date=self.birth_date)


def wrap_sngi_result(sngi_result):
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
