import pytest
from django.db import IntegrityError, transaction

from api_relay_cnav.users.models import User
from tests.users.factories import UserFactory


class TestUserManager:
    def test_create_user(self):
        # Only staff users for the moment
        user = User.objects.create_user(email="test@inclusion.gouv.fr", password="password", is_staff=True)
        assert user.email == "test@inclusion.gouv.fr"
        assert user.is_staff is True
        assert user.is_superuser is False
        assert user.is_active is True
        assert user.check_password("password")
        assert user.has_usable_password()

    def test_create_user_requires_email(self):
        with pytest.raises(ValueError, match="email address must be set"):
            User.objects.create_user(email="", password="password")

    def test_create_user_without_password_is_unusable(self):
        user = User.objects.create_user(email="test@inclusion.gouv.fr", is_staff=True)
        assert user.has_usable_password() is False

    def test_create_user_normalizes_email_domain(self):
        user = User.objects.create_user(email="test@INCLUSION.GOUV.FR", password="password", is_staff=True)
        assert user.email == "test@inclusion.gouv.fr"

    def test_create_superuser(self):
        admin = User.objects.create_superuser(email="admin@inclusion.gouv.fr", password="password")
        assert admin.is_staff is True
        assert admin.is_superuser is True
        assert admin.check_password("password")

    def test_create_superuser_rejects_non_staff(self):
        with pytest.raises(ValueError, match="is_staff=True"):
            User.objects.create_superuser(email="admin@inclusion.gouv.fr", password="password", is_staff=False)

    def test_create_superuser_rejects_non_superuser(self):
        with pytest.raises(ValueError, match="is_superuser=True"):
            User.objects.create_superuser(email="admin@inclusion.gouv.fr", password="password", is_superuser=False)


class TestUserConstraints:
    @pytest.mark.parametrize(
        ("is_staff", "is_superuser", "matched_error"),
        [
            (True, False, None),  # Staff member: allowed
            (True, True, None),  # Staff superuser: allowed
            (False, False, "only_staff_users"),  # Non-staff user
            (False, True, "only_staff_users|staff_and_superusers"),  # A non-staff superuser violates both constraints
        ],
    )
    def test_staff_constraints(self, is_staff, is_superuser, matched_error):
        if matched_error is None:
            assert UserFactory(is_staff=is_staff, is_superuser=is_superuser).pk
        else:
            with pytest.raises(IntegrityError, match=matched_error), transaction.atomic():
                UserFactory(is_staff=is_staff, is_superuser=is_superuser)


class TestEmailCollation:
    """
    The `case_insensitive_unaccent` collation handles both uniqueness and lookups.
    """

    def test_uniqueness_is_case_insensitive(self):
        UserFactory(email="test@inclusion.gouv.fr")
        with pytest.raises(IntegrityError), transaction.atomic():
            UserFactory(email="TEST@inclusion.gouv.fr")

    def test_uniqueness_is_unaccent(self):
        UserFactory(email="léo@inclusion.gouv.fr")
        with pytest.raises(IntegrityError), transaction.atomic():
            UserFactory(email="leo@inclusion.gouv.fr")

    def test_lookup_is_case_insensitive(self):
        user = UserFactory(email="test@inclusion.gouv.fr")
        assert User.objects.get(email="TEST@INCLUSION.GOUV.FR") == user
