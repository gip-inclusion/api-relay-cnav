from __future__ import annotations

import logging

from django.conf import settings
from django.contrib.auth.backends import RemoteUserBackend
from django.contrib.auth.hashers import make_password
from django.db import IntegrityError
from django.http import HttpRequest

from api_relay_cnav.users.models import User


logger = logging.getLogger(__name__)

# Attribute headers set by the Authentik proxy outpost
EMAIL_HEADER = "HTTP_X_AUTHENTIK_EMAIL"
GIVEN_NAME_HEADER = "HTTP_X_AUTHENTIK_GIVEN_NAME"
FAMILY_NAME_HEADER = "HTTP_X_AUTHENTIK_FAMILY_NAME"


class AuthentikRemoteUserBackend(RemoteUserBackend):
    """
    Authenticate the backoffice from Authentik forwardAuth headers.

    Based on the stable uid (stored as User.sub) so an email change in Authentik updates the existing row
    instead of duplicating the account.
    For now every authenticated user is a staff superuser (no groups management yet).
    """

    def authenticate(
        self,
        request: HttpRequest | None,
        remote_user: str | None = None,
        **kwargs: object,
    ) -> User | None:
        if request is None:
            return None
        uid = (remote_user or "").strip()
        if not uid:
            return None

        email = (request.META.get(EMAIL_HEADER) or "").strip()
        defaults: dict[str, object] = {
            "is_staff": True,
            "is_superuser": True,
            "is_active": True,
            "first_name": (request.META.get(GIVEN_NAME_HEADER) or "")[:150],
            "last_name": (request.META.get(FAMILY_NAME_HEADER) or "")[:150],
        }
        if email:
            defaults["email"] = email

        user = User.objects.filter(sub=uid).first()
        if user is not None and all(getattr(user, field) == value for field, value in defaults.items()):
            # User exists but nothing has changed => no writes
            return user if self.user_can_authenticate(user) else None
        if user is None and not (email and settings.AUTHENTIK_CREATE_UNKNOWN_USER):
            # Never create a user when provisioning is disabled or if email is not provided
            return None

        try:
            # Upsert is only based on the sub
            user, _ = User.objects.update_or_create(
                sub=uid,
                defaults=defaults,
                create_defaults={**defaults, "password": make_password(None)},
            )
        except IntegrityError:
            # Typically another user already owns this email
            logger.exception("Could not provision the user for sub=%s", uid)
            return None
        return user if self.user_can_authenticate(user) else None
