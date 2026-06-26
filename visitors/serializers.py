from rest_framework import serializers
from .models import Visitor


class VisitorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Visitor
        fields = [
            'id',
            'first_name',
            'last_name',
            'email',
            'phone_number',
            'organisation',
            'is_active',
            'is_blacklisted',
            'blacklisted_at',
            'blacklisted_reason',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'organisation',
            'is_blacklisted',
            'blacklisted_at',
            'blacklisted_reason',
            'blacklisted_by',
            'created_at',
            'updated_at',
        ]


class VisitorCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Visitor
        fields = [
            'id',
            'first_name',
            'last_name',
            'email',
            'phone_number',
        ]
        read_only_fields = ['id']

    def validate_email(self, value):
        return value.lower()

    def validate_phone_number(self, value):
        if not value.replace('+', '').replace(' ', '').isdigit():
            raise serializers.ValidationError("Enter a valid phone number.")
        return value


class VisitorUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Visitor
        fields = [
            'first_name',
            'last_name',
            'email',
            'phone_number',
        ]

    def validate_email(self, value):
        return value.lower()


class BlacklistVisitorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Visitor
        fields = [
            'is_blacklisted',
            'blacklisted_reason',
        ]

    def validate(self, attrs):
        if attrs.get('is_blacklisted') and not attrs.get('blacklisted_reason'):
            raise serializers.ValidationError({
                "blacklisted_reason": "A reason is required when blacklisting a visitor."
            })
        return attrs


class VisitorMiniSerializer(serializers.ModelSerializer):
    """Lightweight - used when nested inside Visit serializer"""
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Visitor
        fields = [
            'id',
            'full_name',
            'email',
            'phone_number',
        ]

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()


class VisitorSearchSerializer(serializers.Serializer):
    """Used for returning visitor recognition search"""
    query = serializers.CharField(max_length=255)