from django.urls import path

from api_relay_cnav.healthcheck.views import healthcheck


app_name = "healthcheck"


urlpatterns = [
    path("", healthcheck, name="healthcheck"),
]
