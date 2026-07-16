import uuid

import pytest
from django.urls import reverse


def test_GET(api_client):
    response = api_client.get(reverse("api:identity"))
    assert response.status_code == 405


def test_mirror(api_client):
    data = {
        "request_uid": str(uuid.uuid4()),
        "number": "1234567890123",
        "name": "Martin",
        "first_names": "Jean Paul Jacques",
        "sex_code": 1,
        "birth_date": "2000-01-01",
    }
    response = api_client.post(reverse("api:identity"), data=data)
    assert response.status_code == 200
    data.pop("request_uid")
    data["birth_name"] = {"accented": data.pop("name")}
    data["first_names"] = {"accented": data.pop("first_names").split()}
    assert response.json() == {"result_code": 1000, "result_label": "Résultat OK", "infos": data}


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
def test_invalid_numbers(api_client, number, expect_OK):
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
