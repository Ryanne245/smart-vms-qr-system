from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    model = User

    list_display = (
        "email",
        "first_name",
        "last_name",
        "is_staff",
        "is_active",
        "is_superuser",
    )

    list_filter = (
        "is_staff",
        "is_active",
        "is_superuser",
    )

    ordering = ("email",)
    search_fields = ("email", "first_name", "last_name")

    fieldsets = (
        ("Basic Info", {
            "fields": ("email", "first_name", "last_name"),
        }),
        ("Authentication", {
            "fields": ("password",),
        }),
        ("Permissions", {
            "fields": (
                "is_active",
                "is_staff",
                "is_superuser",
                "groups",
                "user_permissions",
            ),
        }),
        ("Important dates", {
            "fields": ("last_login", "date_joined"),
        }),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "email",
                "password1",
                "password2",
                "is_staff",
                "is_active",
            ),
        }),
    )
