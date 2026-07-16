from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from rest_framework import authentication, exceptions, permissions
from rest_framework.request import Request

from api_relay_cnav.utils.token import token_hexdigest


class APIAnonymousUser(AnonymousUser):
    pass


class APIAuthentication(authentication.TokenAuthentication):
    def authenticate_credentials(self, key: str) -> tuple[APIAnonymousUser, None]:
        hashed_key = token_hexdigest(key)
        if hashed_key == settings.HASHED_API_TOKEN:
            return (APIAnonymousUser(), None)
        else:
            raise exceptions.AuthenticationFailed("Invalid token.")


class IsAPIAnonymousUser(permissions.BasePermission):
    def has_permission(self, request: Request, view: object) -> bool:
        return isinstance(request.user, APIAnonymousUser)
