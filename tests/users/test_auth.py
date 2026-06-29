from django.test import RequestFactory

from api_relay_cnav.users.backends import AuthentikRemoteUserBackend
from api_relay_cnav.users.models import User
from tests.users.factories import UserFactory


def _authenticate(uid, email="", given_name="", family_name=""):
    request = RequestFactory().get(
        "/",
        headers={
            "x-authentik-email": email,
            "x-authentik-given-name": given_name,
            "x-authentik-family-name": family_name,
        },
    )
    return AuthentikRemoteUserBackend().authenticate(request, remote_user=uid)


class TestAuthentikRemoteUserBackend:
    def test_creates_a_staff_superuser(self):
        user = _authenticate("uid-1", email="martin@inclusion.gouv.fr", given_name="Martin", family_name="Dupont")
        assert user is not None
        assert user.sub == "uid-1"
        assert user.email == "martin@inclusion.gouv.fr"
        assert user.first_name == "Martin"
        assert user.last_name == "Dupont"
        assert user.is_staff is True
        assert user.is_superuser is True
        assert user.is_active is True
        assert user.has_usable_password() is False
        assert User.objects.count() == 1

    def test_email_change_keeps_the_same_row(self):
        existing = UserFactory(sub="uid-1", email="old@inclusion.gouv.fr")
        user = _authenticate("uid-1", email="new@inclusion.gouv.fr")
        assert user == existing
        assert user.email == "new@inclusion.gouv.fr"
        assert User.objects.count() == 1

    def test_email_conflict_denies_authentication(self):
        UserFactory(sub=None, email="martin@inclusion.gouv.fr")
        assert _authenticate("uid-1", email="martin@inclusion.gouv.fr") is None
        assert User.objects.count() == 1

    def test_blank_uid_returns_none(self):
        assert _authenticate("") is None
        assert User.objects.count() == 0

    def test_missing_email_for_new_user_returns_none(self):
        assert _authenticate("uid-1") is None
        assert User.objects.count() == 0

    def test_missing_email_does_not_overwrite_existing(self):
        UserFactory(sub="uid-1", email="martin@inclusion.gouv.fr")
        user = _authenticate("uid-1", email="")
        assert user is not None
        assert user.email == "martin@inclusion.gouv.fr"

    def test_changed_attribute_is_persisted(self):
        _authenticate("uid-1", email="martin@inclusion.gouv.fr", given_name="Martin", family_name="Dupont")
        _authenticate("uid-1", email="martin@inclusion.gouv.fr", given_name="Martin", family_name="Tournesol")
        assert User.objects.get(sub="uid-1").last_name == "Tournesol"

    def test_unchanged_attributes_are_not_rewritten(self):
        first = _authenticate("uid-1", email="martin@inclusion.gouv.fr", given_name="Martin", family_name="Dupont")
        again = _authenticate("uid-1", email="martin@inclusion.gouv.fr", given_name="Martin", family_name="Dupont")
        assert again.updated_at == first.updated_at
