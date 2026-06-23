import contextlib

import pytest
from django import test
from django.db import IntegrityError, connection
from django.urls import reverse


@pytest.mark.parametrize(
    ("view_name", "postgresql_available", "expect_OK"),
    [
        ("live", True, True),
        ("live", False, True),
        ("ready", True, True),
        ("ready", False, False),
    ],
)
def test_views(client: test.Client, view_name: str, postgresql_available: bool, expect_OK: bool) -> None:
    if postgresql_available:
        cm = contextlib.nullcontext()
    else:

        def _failing_execute(*args) -> None:  # noqa: ANN002
            raise IntegrityError

        cm = connection.execute_wrapper(_failing_execute)

    with cm:
        response = client.get(reverse(f"healthcheck:{view_name}"))

    if expect_OK:
        assert response.status_code == 200
        assert response.content == b"OK"
    else:
        assert response.status_code == 500
        assert response.content == b"Error"
