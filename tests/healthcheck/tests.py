from django import test
from django.db import IntegrityError, connection
from django.urls import reverse


def test_OK(client: test.Client) -> None:
    response = client.get(reverse("healthcheck:healthcheck"))
    assert response.status_code == 200
    assert response.content == b"OK"


def test_KO(client: test.Client) -> None:
    def _failing_execute(*args) -> None:  # noqa: ANN002
        raise IntegrityError

    with connection.execute_wrapper(_failing_execute):
        response = client.get(reverse("healthcheck:healthcheck"))
    assert response.status_code == 500
    assert response.content == b"Error"
