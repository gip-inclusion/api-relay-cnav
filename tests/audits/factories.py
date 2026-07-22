import uuid

import factory

from api_relay_cnav.audits.models import InterOpsCall
from tests.utils.factories import IdentityRequestFactory


class InterOpsCallFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = InterOpsCall
        skip_postgeneration_save = True

    request_uid = factory.LazyFunction(uuid.uuid4)
    request_content = factory.SubFactory(IdentityRequestFactory)
    interops_request_content = "<xml/>"
    interops_response_content = "<xml/>"
    interops_response_status_code = 200
    response_content = {}
