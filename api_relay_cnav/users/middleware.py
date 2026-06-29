from __future__ import annotations

from django.conf import settings
from django.contrib import auth
from django.contrib.auth.middleware import RemoteUserMiddleware
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpRequest


# Stable per-user identifier set by the Authentik proxy outpost
# The proxy is the trust boundary: it *must* strip any client-supplied X-authentik-* header
# and the pod MUST only be reachable through it
UID_HEADER = "HTTP_X_AUTHENTIK_UID"


class AuthentikRemoteUserMiddleware(RemoteUserMiddleware):
    """
    Authenticate every request from the Authentik uid header.

    Declared in MIDDLEWARE unconditionally but acts as a no-op unless settings.AUTHENTIK_FORWARD_AUTH is set
    (the backoffice pod, in prod), so DEV/TEST/API keep the default password/session auth.
    When active, the backend re-runs on each request so attribute changes (email, name) stay in sync.
    If the headers stop identifying a provisionable user, the local session is dropped.
    """

    header = UID_HEADER

    def process_request(self, request: HttpRequest) -> None:
        if not settings.AUTHENTIK_FORWARD_AUTH:
            return

        if not hasattr(request, "user"):
            raise ImproperlyConfigured(
                "AuthentikRemoteUserMiddleware requires django's AuthenticationMiddleware to run first."
            )

        # No forwardAuth header on this request: keep any existing session (persistent)
        if not (uid := request.META.get(self.header)):
            return

        if (user := auth.authenticate(request, remote_user=uid)) is None:
            # Header present but no user could be resolved: drop any previously established session
            if request.user.is_authenticated:
                self._remove_invalid_user(request)
            return

        # Already logged in as this user: refresh attributes without cycling the session
        if request.user.is_authenticated and request.user.pk == user.pk:
            request.user = user
            return

        auth.login(request, user)
