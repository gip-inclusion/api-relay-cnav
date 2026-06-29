from django.contrib import admin
from django.urls import include, path


# URLconf for the "backoffice" pod (behind Authentik forwardAuth)
urlpatterns = [
    path("admin/", admin.site.urls),
    path("healthcheck/", include("api_relay_cnav.healthcheck.urls")),
]
