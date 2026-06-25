from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):

    list_display = (
        'actor',
        'action',
        'target_model',
        'target_id',
        'organisation',
        'ip_address',
        'created_at',
    )

    list_filter = (
        'action',
        'organisation',
        'target_model',
        'created_at',
    )

    search_fields = (
        'actor__email',
        'actor__first_name',
        'actor__last_name',
        'target_id',
        'ip_address',
    )

    ordering = ('-created_at',)
    date_hierarchy = 'created_at'

    readonly_fields = (
        'id',
        'actor',
        'organisation',
        'action',
        'target_model',
        'target_id',
        'details',
        'ip_address',
        'created_at',
    )

    fieldsets = (
        ("Action Info", {
            "fields": (
                'actor',
                'organisation',
                'action',
                'ip_address',
            )
        }),
        ("Target", {
            "fields": (
                'target_model',
                'target_id',
            )
        }),
        ("Details", {
            "fields": (
                'details',
            )
        }),
        ("Timestamp", {
            "fields": (
                'created_at',
            )
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(organisation=request.user.organisation)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False