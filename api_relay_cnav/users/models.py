from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models

from api_relay_cnav.utils.models import TimedModel, UUIDModel


class UserManager(BaseUserManager[AbstractUser]):
    """
    Custom user manager where email is the unique identifiers for authentication and user creation.
    """

    use_in_migrations = True

    def _create_user(
        self,
        email: str,
        password: str | None,
        **extra_fields: object,
    ) -> AbstractUser:
        if not email:
            raise ValueError("The email address must be set.")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(
        self,
        email: str,
        password: str | None = None,
        **extra_fields: object,
    ) -> AbstractUser:
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(
        self,
        email: str,
        password: str,
        **extra_fields: object,
    ) -> AbstractUser:
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


class User(UUIDModel, AbstractUser, TimedModel):
    date_joined = None
    username = None

    # Non-deterministic ICU collation: case- and accent-insensitive (level1).
    # Level1 is intentional: despite the RFC, most mail providers consider unaccented values unique in the local-part.
    email = models.EmailField("adresse email", db_collation="case_insensitive_unaccent", unique=True)
    sub = models.CharField("identifiant Authentik", max_length=64, null=True, unique=True)  # noqa: DJ001

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta(AbstractUser.Meta):
        constraints = [
            models.CheckConstraint(
                name="staff_and_superusers",
                violation_error_message="Seul un utilisateur du staff peut avoir is_superuser de vrai.",
                condition=models.Q(is_superuser=False) | models.Q(is_staff=True),
            ),
            models.CheckConstraint(
                name="only_staff_users",
                violation_error_message="Seuls des utilisateurs staff sont autorisés à ce stade.",
                condition=models.Q(is_staff=True),
            ),
        ]
