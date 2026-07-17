from api_relay_cnav import urls_api, urls_backoffice


# Combined urlconf (SERVICE=ALL): serves all services from one process in DEV/TEST.
# API first: its "" index would eventually shadow the backoffice's "" redirect.
urlpatterns = [
    *urls_api.urlpatterns,
    *urls_backoffice.urlpatterns,
]
