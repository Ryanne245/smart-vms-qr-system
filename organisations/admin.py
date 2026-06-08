from django.contrib import admin
from .models import Organisation, OrganisationSettings
# Register your models here.

@admin.register(Organisation)
class OrganisationAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone_number', 'is_active', 'created_at', 'updated_at')
    search_fields = ('name', 'email', 'phone_number')
    list_filter = ('is_active', 'created_at')

@admin.register(OrganisationSettings)
class OrganisationSettingsAdmin(admin.ModelAdmin):
    search_fields = ('key',)
    list_filter = ('organisation',)