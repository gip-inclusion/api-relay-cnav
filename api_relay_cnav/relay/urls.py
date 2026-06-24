from django.urls import path

from api_relay_cnav.relay.views import IdentityView


app_name = "relay"

urlpatterns = [
    path("identity/", IdentityView.as_view(), name="identity"),
]
