from django.contrib import admin
from .models import Organisation, OrganisationSettings
# Register your models here.

@admin.register(Organisation)
class OrganisationAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone_number', 'is_active', 'created_at', 'updated_at')
    search_fields = ('name', 'email', 'phone_number')
    list_filter = ('is_active', 'created_at')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(OrganisationSettings)
class OrganisationSettingsAdmin(admin.ModelAdmin):
    list_display = (
        'organisation',
        'default_visit_duration',
        'require_host_approval',
        'allow_multiple_active_visits',
        'emergency_lockdown',
    )
    search_fields = ('organisation__name',)
    list_filter = ('organisation', 'require_host_approval', 'emergency_lockdown')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ("Organisation", {
            "fields": ("organisation",)
        }),
        ("Visit Settings", {
            "fields": (
                "default_visit_duration",
                "require_host_approval",
                "allow_multiple_active_visits",
                "notify_host_on_checkin",
                "notify_before_expiry_minutes",
            )
        }),
        ("Overstay & Security", {
            "fields": (
                "overstay_grace_period_minutes",
                "emergency_lockdown",
            )
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at")
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