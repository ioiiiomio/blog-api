from typing import Any

from unfold.admin import ModelAdmin
from unfold.contrib.filters.admin import BooleanRadioFilter
from unfold.decorators import display, action
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

from django.contrib import messages
from django.contrib.admin import register, site
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.models import Group
from django.db.models import Count, QuerySet
from django.http import HttpRequest

from apps.auths.models import User


class BlogUserCreationForm(UserCreationForm):
    usable_password = None

    class Meta:
        model = User
        fields = ("email", "first_name", "last_name")

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.fields["password1"].required = True
        self.fields["password2"].required = True


class BlogUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = "__all__"


@register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    """User model admin configuration class."""
    form = BlogUserChangeForm
    add_form = BlogUserCreationForm
    change_password_form = AdminPasswordChangeForm

    list_display = (
        "user_header",
        "active_label",
        "staff_label",
        "posts_count",
        "last_login",
    )

    list_filter = (
        ("is_staff", BooleanRadioFilter),
        ("is_active", BooleanRadioFilter),
    )

    list_filter_submit = True

    search_fields = ("email", "first_name", "last_name")
    ordering = ("id",)
    readonly_fields = ("last_login",)
    filter_horizontal = ("groups", "user_permissions")
    actions = ("activate_users", "deactivate_users")
    list_per_page = 50

    fieldsets = (
    (
        "Personal info",
        {
            "classes": ["tab"],
            "fields": ("email", "password", ("first_name", "last_name")),
        },
    ),
    (
        "Permissions",
        {
            "classes": ["tab"],
            "fields": (
                "is_active", "is_staff", "is_superuser", "groups", "user_permissions",
            ),
        },
    ),
    (
        "Important dates",
        {
            "classes": ["tab"],
            "fields": ("last_login",),
        },
    ),
)

    add_fieldsets = (
    (
        None,
        {
            "classes": ["wide"],
            "fields": (
                "email",
                ("first_name", "last_name"),
                "password1",
                "password2",
            ),
        },
    ),
)

    def get_queryset(self, request: HttpRequest) -> QuerySet[User]:
        return super().get_queryset(request).annotate(_posts_count=Count("posts"))

    @display(description="User", header=True, ordering="last_name")
    def user_header(self, obj: User) -> list[str]:
        initial = f"{obj.first_name[:1]} {obj.last_name[:1]}"
        return [f"{obj.first_name} {obj.last_name}", obj.email, initial]

    @display(description="Active", label={True: "success", False: "danger"})
    def active_label(self, obj: User) -> tuple[bool, str]:
        return obj.is_active, "Active" if obj.is_active else "Inactive"

    @display(description="Staff", label={True: "info", False: "danger"})
    def staff_label(self, obj: User) -> tuple[bool, str]:
        return obj.is_staff, "Staff" if obj.is_staff else "User"

    @display(description="Posts", ordering="_posts_count")
    def posts_count(self, obj: User) -> int:
        return obj._posts_count

    @action(description="Activate selected users", icon="check_circle")
    def activate_users(self, request: HttpRequest, queryset: QuerySet[User]) -> None:
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} user(s) activated.", messages.SUCCESS)

    @action(description="Deactivate selected users", icon="block")
    def deactivate_users(self, request: HttpRequest, queryset: QuerySet[User]) -> None:
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} user(s) deactivated.", messages.WARNING)


site.unregister(Group)


@register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass
