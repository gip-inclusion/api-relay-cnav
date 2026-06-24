from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path("admin/", admin.site.urls),
    path("relay/", include("api_relay_cnav.relay.urls")),
]
