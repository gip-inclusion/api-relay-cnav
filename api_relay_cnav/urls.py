from django.urls import include, path

from api_relay_cnav import urls_backoffice


# Combined urlconf (SERVICE=ALL): serves all services from one process in DEV/TEST.
# API first (when it lands): its "" index would eventually shadow the backoffice's "" redirect.
urlpatterns = [
    path("api/", include("api_relay_cnav.api.urls")),
    *urls_backoffice.urlpatterns,
]
