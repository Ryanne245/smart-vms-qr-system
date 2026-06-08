from django.contrib import admin
from .models import Visitor


@admin.register(Visitor)
class VisitorAdmin(admin.ModelAdmin):

    # Columns shown in the admin table
    list_display = (
        "first_name",
        "last_name",
        "email",
        "phone_number",
        "organisation",
        "is_active",
        "created_at",
    )

    # Filters on the right sidebar
    list_filter = (
        "organisation",
        "is_active",
        "created_at",
    )

    # Search bar fields
    search_fields = (
        "first_name",
        "last_name",
        "email",
        "phone_number",
    )

    # Default ordering
    ordering = ("-created_at",)

    # Fields that cannot be edited manually
    readonly_fields = ("created_at", "updated_at")

    # Organize the form layout
    fieldsets = (
        ("Visitor Information", {
            "fields": (
                "first_name",
                "last_name",
                "email",
                "phone_number",
            )
        }),
        ("Organisation", {
            "fields": (
                "organisation",
            )
        }),
        ("Status", {
            "fields": (
                "is_active",
            )
        }),
        ("Timestamps", {
            "fields": (
                "created_at",
                "updated_at",
            )
        }),
    )

    # Restrict visitors by organisation
    def get_queryset(self, request):
        qs = super().get_queryset(request)

        if request.user.is_superuser:
            return qs

        return qs.filter(organisation=request.user.organisation)

    # Automatically assign organisation on save
    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser:
            obj.organisation = request.user.organisation

        super().save_model(request, obj, form, change)