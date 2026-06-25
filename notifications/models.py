import uuid
from django.db import models
from django.conf import settings
from visits.models import Visit
from organisations.models import Organisation
from django.contrib.auth import get_user_model

User = get_user_model()


class Notification(models.Model):

    class Type(models.TextChoices):
        VISIT_CREATED = "VISIT_CREATED", "Visit Created"
        VISIT_APPROVED = "VISIT_APPROVED", "Visit Approved"
        VISIT_REJECTED = "VISIT_REJECTED", "Visit Rejected"
        VISITOR_CHECKED_IN = "VISITOR_CHECKED_IN", "Visitor Checked In"
        VISITOR_CHECKED_OUT = "VISITOR_CHECKED_OUT", "Visitor Checked Out"
        VISIT_OVERSTAY = "VISIT_OVERSTAY", "Visit Overstay"
        VISIT_CANCELLED = "VISIT_CANCELLED", "Visit Cancelled"
        VISIT_EXPIRED = "VISIT_EXPIRED", "Visit Expired"
        VISITOR_BLACKLISTED = "VISITOR_BLACKLISTED", "Visitor Blacklisted"

    class Channel(models.TextChoices):
        IN_APP = "IN_APP", "In App"
        EMAIL = "EMAIL", "Email"

    class DeliveryStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        SENT = "SENT", "Sent"
        FAILED = "FAILED", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    visit = models.ForeignKey(Visit, on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=30, choices=Type.choices)
    channel = models.CharField(max_length=10, choices=Channel.choices, default=Channel.IN_APP)
    delivery_status = models.CharField(max_length=10, choices=DeliveryStatus.choices, default=DeliveryStatus.PENDING)
    message = models.TextField()
    failed_reason = models.TextField(blank=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.notification_type} -> {self.recipient} ({self.channel})"

    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['organisation']),
            models.Index(fields=['delivery_status']),
            models.Index(fields=['channel']),
        ]