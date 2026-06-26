from rest_framework import serializers
from .models import AuditLog
from user.serializers import UserMiniSerializer


class AuditLogSerializer(serializers.ModelSerializer):
    actor = UserMiniSerializer(read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            'id',
            'actor',
            'organisation',
            'action',
            'target_model',
            'target_id',
            'details',
            'ip_address',
            'created_at',
        ]
        read_only_fields = [
            'id',
            'actor',
            'organisation',
            'action',
            'target_model',
            'target_id',
            'details',
            'ip_address',
            'created_at',
        ]


class AuditLogMiniSerializer(serializers.ModelSerializer):
    """Lightweight - for listing"""
    class Meta:
        model = AuditLog
        fields = [
            'id',
            'action',
            'target_model',
            'target_id',
            'created_at',
        ]


class AuditLogFilterSerializer(serializers.Serializer):
    """Used to filter audit logs"""
    action = serializers.ChoiceField(
        choices=AuditLog.Action.choices,
        required=False
    )
    target_model = serializers.CharField(required=False)
    target_id = serializers.CharField(required=False)
    from_date = serializers.DateTimeField(required=False)
    to_date = serializers.DateTimeField(required=False)