from django.contrib.admin import register
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from apps.auths.models import User


@register(User)
class UserAdmin(BaseUserAdmin):
    """User model admin configuration class."""

    list_display = (
        "id",
        "email",
        "first_name",
        "last_name",
        "is_active",
        "is_staff",
    )
    list_display_links = (
        "id",
        "email",
    )
    list_filter = (
        "is_staff",
        "is_active",
    )
    search_fields = (
        "email",
        "first_name",
        "last_name",
    )
    ordering = (
        "id",
    )
    readonly_fields = (
        "last_login",
    )
    filter_horizontal = (
        "groups",
        "user_permissions",
    )
    fieldsets = (
        (
            "General information",
            {
                "fields": (
                    "email",
                    "password",
                    ("first_name", "last_name"),
                )
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    ("is_staff", "is_active", "is_superuser"),
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (
            "Date and time information",
            {
                "fields": (
                    "last_login",
                )
            },
        ),
    )
    # form for the "Add user" page
    add_fieldsets = (
        (
            None,
            {
                "fields": (
                    "email",
                    ("first_name", "last_name"),
                    "password1",
                    "password2",
                )
            },
        ),
    )
    list_per_page = 50
