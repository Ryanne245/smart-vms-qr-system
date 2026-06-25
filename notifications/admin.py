from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):

    list_display = (
        'recipient',
        'notification_type',
        'channel',
        'delivery_status',
        'is_read',
        'organisation',
        'created_at',
    )

    list_filter = (
        'notification_type',
        'channel',
        'delivery_status',
        'is_read',
        'organisation',
    )

    search_fields = (
        'recipient__email',
        'recipient__first_name',
        'recipient__last_name',
        'message',
    )

    ordering = ('-created_at',)

    readonly_fields = (
        'id',
        'created_at',
        'updated_at',
        'read_at',
    )

    fieldsets = (
        ("Notification Info", {
            "fields": (
                'recipient',
                'organisation',
                'visit',
                'notification_type',
                'message',
            )
        }),
        ("Delivery", {
            "fields": (
                'channel',
                'delivery_status',
                'failed_reason',
            )
        }),
        ("Read Status", {
            "fields": (
                'is_read',
                'read_at',
            )
        }),
        ("Timestamps", {
            "fields": (
                'created_at',
                'updated_at',
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