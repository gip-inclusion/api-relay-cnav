from django.urls import include, path


# URLconf for the "API" pod (publicly accessible from authorized IPs)
urlpatterns = [
    path("healthcheck/", include("api_relay_cnav.healthcheck.urls")),
    path("", include("api_relay_cnav.api.urls")),
]
