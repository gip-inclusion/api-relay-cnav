from django.urls import reverse


def test_openapi_schema(client):
    response = client.get(reverse("api:openapi_schema"))
    assert response.headers["Content-Type"] == "application/vnd.oai.openapi; charset=utf-8"
    assert b"API - Relai vers la CNAV" in response.content


def failing_function(*args, **kwargs):
    raise Exception("Something bad")


def test_error_handling(api_client, mocker, settings):
    api_client.raise_request_exception = False
    settings.DRF_STANDARDIZED_ERRORS = getattr(settings, "DRF_STANDARDIZED_ERRORS", {}) | {
        "ENABLE_IN_DEBUG_FOR_UNHANDLED_EXCEPTIONS": True
    }
    mocker.patch("api_relay_cnav.api.serializers.IdentitySerializer.is_valid", failing_function)

    response = api_client.post(reverse("api:identity"))
    assert response.status_code == 500
    assert response.json() == {
        "errors": [
            {
                "attr": None,
                "code": "error",
                "detail": "Server Error (500)",
            },
        ],
        "type": "server_error",
    }
