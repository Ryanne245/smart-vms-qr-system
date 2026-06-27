from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from .models import Notification
from .serializers import (
    NotificationSerializer,
    NotificationMiniSerializer,
    MarkNotificationReadSerializer,
    MarkAllNotificationsReadSerializer,
)


class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        notifications = Notification.objects.filter(
            recipient=request.user
        ).order_by('-created_at')

        # Filters
        is_read = request.query_params.get('is_read')
        notification_type = request.query_params.get('type')
        channel = request.query_params.get('channel')

        if is_read is not None:
            notifications = notifications.filter(
                is_read=is_read.lower() == 'true'
            )
        if notification_type:
            notifications = notifications.filter(
                notification_type=notification_type.upper()
            )
        if channel:
            notifications = notifications.filter(
                channel=channel.upper()
            )

        serializer = NotificationMiniSerializer(notifications, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class NotificationUnreadCountView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        count = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()
        return Response(
            {"unread_count": count},
            status=status.HTTP_200_OK
        )


class NotificationMarkReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, notification_id):
        try:
            notification = Notification.objects.get(
                id=notification_id,
                recipient=request.user
            )
        except Notification.DoesNotExist:
            return Response(
                {"detail": "Notification not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = MarkNotificationReadSerializer()
        serializer.save(notification=notification)
        return Response(
            {"detail": "Notification marked as read."},
            status=status.HTTP_200_OK
        )


class NotificationMarkAllReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = MarkAllNotificationsReadSerializer()
        serializer.save(user=request.user)
        return Response(
            {"detail": "All notifications marked as read."},
            status=status.HTTP_200_OK
        )
class NotificationDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, notification_id):
        try:
            notification = Notification.objects.get(
                id=notification_id,
                recipient=request.user
            )
        except Notification.DoesNotExist:
            return Response(
                {"detail": "Notification not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = NotificationSerializer(notification)
        return Response(serializer.data, status=status.HTTP_200_OK)