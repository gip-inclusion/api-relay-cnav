import pytest
from django.db import connections
from django.test import Client
from drf_standardized_errors.handler import ExceptionHandler


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Automatically add pytest db marker if needed."""
    for item in items:
        markers = {marker.name for marker in item.iter_markers()}
        if "no_django_db" not in markers and "django_db" not in markers:
            item.add_marker(pytest.mark.django_db)


@pytest.fixture
def api_client():
    from rest_framework.test import APIClient

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Token Secret-Token")
    return client


@pytest.fixture
def backoffice_client(settings):
    """Test client hitting the backoffice urlconf with Authentik forwardAuth active."""
    settings.ROOT_URLCONF = "api_relay_cnav.urls_backoffice"
    settings.AUTHENTIK_FORWARD_AUTH = True
    settings.AUTHENTICATION_BACKENDS = ["api_relay_cnav.users.backends.AuthentikRemoteUserBackend"]
    return Client()


# Do not rollback non_atomic_requests views
def smarter_set_rollback(self):
    for db in connections.all():
        if db.settings_dict["ATOMIC_REQUESTS"] and db.in_atomic_block and not db.atomic_blocks[-1]._from_testcase:
            db.set_rollback(True)


@pytest.fixture
def smarter_drf_set_rollback(monkeypatch):
    monkeypatch.setattr(ExceptionHandler, "set_rollback", smarter_set_rollback)
