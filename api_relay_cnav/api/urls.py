from django.urls import path
from drf_spectacular.views import SpectacularAPIView

from api_relay_cnav.api.views import IdentityView


app_name = "api"

urlpatterns = [
    path(
        "openapi/",
        SpectacularAPIView.as_view(),
        name="openapi_schema",
    ),
    path("identity/", IdentityView.as_view(), name="identity"),
]
