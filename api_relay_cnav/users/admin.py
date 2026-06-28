from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from api_relay_cnav.users import models


@admin.register(models.User)
class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (_("Personal info"), {"fields": ("id", "sub", "email", "first_name", "last_name")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "created_at", "updated_at")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "usable_password", "password1", "password2"),
            },
        ),
    )
    list_display = (
        "email",
        "first_name",
        "last_name",
        "last_login",
    )
    list_display_links = ("email",)
    search_fields = ("=email", "first_name", "last_name")
    readonly_fields = ("id", "sub", "email", "last_login", "created_at", "updated_at")
    ordering = ("-pk",)
