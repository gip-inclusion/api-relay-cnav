from django.urls import reverse

from tests.users.factories import UserFactory


class TestUserAdmin:
    def test_changelist(self, admin_client):
        UserFactory()
        response = admin_client.get(reverse("admin:users_user_changelist"))
        assert response.status_code == 200

    def test_change_view(self, admin_client):
        user = UserFactory()
        response = admin_client.get(reverse("admin:users_user_change", args=[user.pk]))
        assert response.status_code == 200

    def test_add_view(self, admin_client):
        response = admin_client.get(reverse("admin:users_user_add"))
        assert response.status_code == 200
