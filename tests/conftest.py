import pytest
from django.test import Client


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
