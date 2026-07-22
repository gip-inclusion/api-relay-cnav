import uuid

import httpx
import pytest
import respx
from django.urls import reverse

from api_relay_cnav.audits.models import InterOpsCall
from api_relay_cnav.utils.interops import InterOpsExchange, InterOpsResult
from tests.utils.factories import (
    IdentityInterOpsResponseContentFactory,
    IdentityRequestFactory,
    fake_interops_identity_response,
)


def test_GET(api_client):
    response = api_client.get(reverse("api:identity"))
    assert response.status_code == 405


def test_missing_token(api_client):
    api_client.credentials()  # Flush default credentials
    response = api_client.post(reverse("api:identity"), data={})
    assert response.status_code == 401


def test_wrong_token(api_client):
    api_client.credentials(HTTP_AUTHORIZATION="Token Wrong-Token")
    response = api_client.post(reverse("api:identity"), data={})
    assert response.status_code == 401


@respx.mock
def test_OK(api_client, settings):
    settings.INTEROPS_BASE_URL = "http://interops"
    settings.INTEROPS_IDENTITY_PATH = "/identity"
    interops_data = IdentityInterOpsResponseContentFactory(
        birth_name="Millet",
        first_names="Camille François",
    )
    interops_response_content = fake_interops_identity_response(**interops_data)
    interops_route = respx.post("http://interops/identity").respond(200, content=interops_response_content)

    data = {
        "request_uid": str(uuid.uuid4()),
        "number": interops_data["number"],
        "name": "millet",
        "first_names": "camille",
        "sex_code": interops_data["sex_code"],
        "birth_date": interops_data["birth_date"].isoformat(),
    }
    response = api_client.post(reverse("api:identity"), data=data)
    assert response.status_code == 200
    [http_post] = interops_route.calls
    expected_response = {
        "result_code": 1000,
        "result_label": "Résultat OK",
        "infos": {
            "number": interops_data["number"],
            "birth_date": interops_data["birth_date"].isoformat(),
            "birth_place": interops_data["birth_place"],
            "sex_code": interops_data["sex_code"],
            "birth_name": {"accented": "Millet", "filtered": "MILLET"},
            "common_name": None,
            "marital_name": None,
            "first_names": {"accented": ["Camille", "François"], "filtered": ["CAMILLE", "FRANOIS"]},
            "death_date": None,
            "number_history": [],
        },
    }
    assert response.json() == expected_response
    call = InterOpsCall.objects.get()
    assert call.request_uid == uuid.UUID(data["request_uid"])
    assert call.request_content == data
    assert call.interops_request_content == http_post.request.content.decode()
    assert call.interops_response_content == interops_response_content
    assert call.interops_response_status_code == 200
    assert call.response_content == expected_response


@respx.mock
@pytest.mark.usefixtures("smarter_drf_set_rollback")
def test_interops_unavailable(api_client, settings):
    api_client.raise_request_exception = False
    settings.INTEROPS_BASE_URL = "http://interops"
    settings.INTEROPS_IDENTITY_PATH = "/identity"
    interops_route = respx.post("http://interops/identity").mock(side_effect=httpx.ConnectError)

    response = api_client.post(reverse("api:identity"), data=IdentityRequestFactory())
    assert response.status_code == 503
    assert interops_route.call_count == 1
    assert response.json() == {
        "errors": [
            {
                "attr": None,
                "code": "interops-communication-error",
                "detail": "Error contacting InterOps: Mock Error",
            }
        ],
        "type": "server_error",
    }
    assert not InterOpsCall.objects.exists()


@respx.mock
@pytest.mark.usefixtures("smarter_drf_set_rollback")
def test_interops_invalid_response(api_client, settings):
    api_client.raise_request_exception = False
    settings.INTEROPS_BASE_URL = "http://interops"
    settings.INTEROPS_IDENTITY_PATH = "/identity"
    interops_response_content = "Je suis une théière"
    interops_route = respx.post("http://interops/identity").respond(418, content=interops_response_content)

    request_content = IdentityRequestFactory()
    request_content["birth_date"] = request_content["birth_date"].isoformat()
    request_content["request_uid"] = str(request_content["request_uid"])

    response = api_client.post(reverse("api:identity"), data=request_content)
    assert response.status_code == 500
    [http_post] = interops_route.calls
    assert response.json() == {
        "errors": [{"attr": None, "code": "error", "detail": "Server Error (500)"}],
        "type": "server_error",
    }
    call = InterOpsCall.objects.get()
    assert call.request_uid == uuid.UUID(request_content["request_uid"])
    assert call.request_content == request_content
    assert call.interops_request_content == http_post.request.content.decode()
    assert call.interops_response_content == interops_response_content
    assert call.interops_response_status_code == 418
    assert call.response_content is None


@pytest.mark.usefixtures("smarter_drf_set_rollback")
def test_errors(api_client):
    data = {
        "request_uid": "",  # Missing
        "number": "1234",  # Too short
        "name": "Martin" * 20,  # Too long
        "first_names": "Jean Paul Jacques" * 10,  # Too long
        "sex_code": 3,  # Invalid
        "birth_date": "1er janvier 2000",  # Bad format
    }
    response = api_client.post(reverse("api:identity"), data=data)
    assert response.status_code == 400
    assert response.json() == {
        "errors": [
            {
                "attr": "request_uid",
                "code": "invalid",
                "detail": "Doit être un UUID valide.",
            },
            {
                "attr": "number",
                "code": "min_length",
                "detail": "Assurez-vous que ce champ comporte au moins 13\xa0caractères.",
            },
            {
                "attr": "name",
                "code": "max_length",
                "detail": "Assurez-vous que ce champ comporte au plus 63\xa0caractères.",
            },
            {
                "attr": "first_names",
                "code": "max_length",
                "detail": "Assurez-vous que ce champ comporte au plus 50\xa0caractères.",
            },
            {
                "attr": "sex_code",
                "code": "max_value",
                "detail": "Assurez-vous que cette valeur est inférieure ou égale à 2.",
            },
            {
                "attr": "birth_date",
                "code": "invalid",
                "detail": "La date n'a pas le bon format. Utilisez un des formats suivants\xa0: YYYY-MM-DD.",
            },
        ],
        "type": "validation_error",
    }
    assert not InterOpsCall.objects.exists()


@pytest.mark.parametrize(
    ("number", "expect_OK"),
    [
        ("1234567890123", True),
        ("1234567890000", False),  # Ending with 000
        ("0234567890123", False),  # Starting with 0
        ("123452A890123", True),
        ("123453A890123", False),  # A (and B) can only be used with 2 for Corsica
    ],
)
@pytest.mark.usefixtures("smarter_drf_set_rollback")
def test_invalid_numbers(api_client, number, expect_OK, mocker):
    # Skip InterOps call but it might be simpler to provide a valid response ?
    mocker.patch(
        "api_relay_cnav.utils.interops.InterOpsClient.identity",
        return_value=InterOpsExchange(request="", response="", response_status_code=200),
    )
    mocker.patch(
        "api_relay_cnav.api.views.parse_response",
        return_value=InterOpsResult(code=1000, label="OK"),
    )
    response = api_client.post(
        reverse("api:identity"),
        data={
            "request_uid": str(uuid.uuid4()),
            "name": "Martin",
            "first_names": "Jean Paul Jacques",
            "sex_code": 1,
            "birth_date": "2000-01-01",
            "number": number,
        },
    )
    if expect_OK:
        assert response.status_code == 200
        assert InterOpsCall.objects.exists()
    else:
        assert response.status_code == 400
        assert response.json() == {
            "errors": [
                {
                    "attr": "number",
                    "code": "invalid",
                    "detail": "Numéro invalide.",
                },
            ],
            "type": "validation_error",
        }
        assert not InterOpsCall.objects.exists()
