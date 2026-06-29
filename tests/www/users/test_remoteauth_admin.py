from django.urls import reverse

from api_relay_cnav.users.models import User


HEADERS = {"x-authentik-uid": "uid-1", "x-authentik-email": "martin@inclusion.gouv.fr"}


class TestBackofficeRemoteAuth:
    def test_headers_grant_admin_access(self, backoffice_client):
        response = backoffice_client.get(reverse("admin:index"), headers=HEADERS)
        assert response.status_code == 200
        assert response.wsgi_request.user.is_superuser is True
        assert User.objects.filter(sub="uid-1").exists()

    def test_no_headers_redirects_to_login(self, backoffice_client):
        response = backoffice_client.get(reverse("admin:index"))
        assert response.status_code == 302

    def test_missing_header_drops_existing_session(self, backoffice_client):
        backoffice_client.get(reverse("admin:index"), headers=HEADERS)
        response = backoffice_client.get(reverse("admin:index"))
        assert response.status_code == 302
        assert response.wsgi_request.user.is_authenticated is False

    def test_email_change_keeps_a_single_account(self, backoffice_client):
        backoffice_client.get(reverse("admin:index"), headers=HEADERS)
        backoffice_client.get(reverse("admin:index"), headers=HEADERS | {"x-authentik-email": "new@inclusion.gouv.fr"})
        assert User.objects.filter(sub="uid-1").count() == 1
        assert User.objects.get(sub="uid-1").email == "new@inclusion.gouv.fr"

    def test_logout_redirects_to_authentik(self, backoffice_client, settings):
        settings.LOGOUT_REDIRECT_URL = "https://auth.inclusion/flows/-/default/invalidation/"
        response = backoffice_client.post(reverse("admin:logout"), headers=HEADERS)
        assert response.status_code == 302
        assert response.headers["Location"] == settings.LOGOUT_REDIRECT_URL
