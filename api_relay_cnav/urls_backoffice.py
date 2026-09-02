from django.contrib import admin
from django.contrib.auth.decorators import login_not_required
from django.urls import include, path
from django.views.generic.base import RedirectView


# URLconf for the "backoffice" pod (behind Authentik forwardAuth)
urlpatterns = [
    # Temporary home: the admin is the only module for now
    path("", login_not_required(RedirectView.as_view(pattern_name="admin:index"))),
    path("admin/", admin.site.urls),
    path("healthcheck/", include("api_relay_cnav.healthcheck.urls")),
]
