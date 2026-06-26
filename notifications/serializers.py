from rest_framework import serializers
from django.utils import timezone
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            'id',
            'recipient',
            'visit',
            'organisation',
            'notification_type',
            'channel',
            'delivery_status',
            'message',
            'failed_reason',
            'is_read',
            'read_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'recipient',
            'visit',
            'organisation',
            'notification_type',
            'channel',
            'delivery_status',
            'message',
            'failed_reason',
            'read_at',
            'created_at',
            'updated_at',
        ]


class MarkNotificationReadSerializer(serializers.ModelSerializer):
    """Used to mark a single notification as read"""
    class Meta:
        model = Notification
        fields = ['is_read']

    def save(self, notification):
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save(update_fields=['is_read', 'read_at', 'updated_at'])
        return notification


class MarkAllNotificationsReadSerializer(serializers.Serializer):
    """Mark all notifications as read for a user"""
    def save(self, user):
        Notification.objects.filter(
            recipient=user,
            is_read=False
        ).update(
            is_read=True,
            read_at=timezone.now()
        )


class NotificationMiniSerializer(serializers.ModelSerializer):
    """Lightweight - for listing unread notifications"""
    class Meta:
        model = Notification
        fields = [
            'id',
            'notification_type',
            'message',
            'is_read',
            'created_at',
        ]