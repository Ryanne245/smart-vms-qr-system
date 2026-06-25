from django.contrib import admin
from .models import Visit


@admin.register(Visit)
class VisitAdmin(admin.ModelAdmin):

    list_display = (
        "visitor",
        "host",
        "organisation",
        "status",
        "purpose",
        "checked_in_at",
        "checked_out_at",
        "overstay_flagged",
        "created_at",
    )

    list_filter = (
        "status",
        "organisation",
        "overstay_flagged",
        "created_at",
    )

    search_fields = (
        "visitor__first_name",
        "visitor__last_name",
        "visitor__email",
        "host__first_name",
        "host__last_name",
        "host__email",
    )

    ordering = ("-created_at",)

    readonly_fields = (
        "id",
        "qr_code_token",
        "qr_generated_at",
        "qr_expires_at",
        "checked_in_at",
        "checked_out_at",
        "host_responded_at",
        "overstay_flagged_at",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        ("Visit Information", {
            "fields": (
                "visitor",
                "host",
                "organisation",
                "registered_by",
                "purpose",
                "status",
            )
        }),
        ("QR Code", {
            "fields": (
                "qr_code_token",
                "qr_code_image",
                "qr_generated_at",
                "qr_expires_at",
            )
        }),
        ("Timing", {
            "fields": (
                "expected_duration",
                "scheduled_time",
                "checked_in_at",
                "checked_out_at",
                "host_responded_at",
            )
        }),
        ("Check In/Out Tracking", {
            "fields": (
                "checked_in_by",
                "checked_out_by",
            )
        }),
        ("Cancellation", {
            "fields": (
                "cancelled_by",
                "cancellation_reason",
            )
        }),
        ("Rejection", {
            "fields": (
                "rejection_reason",
            )
        }),
        ("Overstay", {
            "fields": (
                "overstay_flagged",
                "overstay_flagged_at",
            )
        }),
        ("Timestamps", {
            "fields": (
                "created_at",
                "updated_at",
            )
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(organisation=request.user.organisation)

    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser:
            obj.organisation = request.user.organisation
        super().save_model(request, obj, form, change)