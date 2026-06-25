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
        "role",
        "organisation",
        "department",
        "is_staff",
        "is_active",
        "is_superuser",
    )

    list_filter = (
        "role",
        "organisation",
        "is_staff",
        "is_active",
        "is_superuser",
    )

    ordering = ("email",)
    search_fields = ("email", "first_name", "last_name", "department")

    fieldsets = (
        ("Basic Info", {
            "fields": ("email", "first_name", "last_name", "role", "organisation", "department"),
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
                "role",
                "organisation",
                "department",
                "is_staff",
                "is_active",
            ),
        }),
    )

    readonly_fields = ("last_login", "date_joined")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(organisation=request.user.organisation)

    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser:
            obj.organisation = request.user.organisation
        super().save_model(request, obj, form, change)