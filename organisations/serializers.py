from rest_framework import serializers
from .models import Organisation, OrganisationSettings


class OrganisationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organisation
        fields = [
            'id',
            'name',
            'address',
            'email',
            'phone_number',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class OrganisationSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganisationSettings
        fields = [
            'id',
            'organisation',
            'default_visit_duration',
            'require_host_approval',
            'notify_host_on_checkin',
            'allow_multiple_active_visits',
            'notify_before_expiry_minutes',
            'overstay_grace_period_minutes',
            'emergency_lockdown',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'organisation', 'created_at', 'updated_at']


class OrganisationDetailSerializer(serializers.ModelSerializer):
    settings = OrganisationSettingsSerializer(read_only=True)

    class Meta:
        model = Organisation
        fields = [
            'id',
            'name',
            'address',
            'email',
            'phone_number',
            'is_active',
            'settings',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']