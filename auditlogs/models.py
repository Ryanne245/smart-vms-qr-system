import uuid
from django.db import models
from django.conf import settings
from organisations.models import Organisation
from django.contrib.auth import get_user_model

User = get_user_model()


class AuditLog(models.Model):

    class Action(models.TextChoices):
        # Visit actions
        VISIT_CREATED = "VISIT_CREATED", "Visit Created"
        VISIT_APPROVED = "VISIT_APPROVED", "Visit Approved"
        VISIT_REJECTED = "VISIT_REJECTED", "Visit Rejected"
        VISIT_CANCELLED = "VISIT_CANCELLED", "Visit Cancelled"
        VISIT_EXPIRED = "VISIT_EXPIRED", "Visit Expired"
        VISIT_CHECKED_IN = "VISIT_CHECKED_IN", "Visit Checked In"
        VISIT_CHECKED_OUT = "VISIT_CHECKED_OUT", "Visit Checked Out"
        VISIT_OVERSTAY_FLAGGED = "VISIT_OVERSTAY_FLAGGED", "Visit Overstay Flagged"
        NOTES_ADDED = "NOTES_ADDED", "Notes Added"

        # Visitor actions
        VISITOR_CREATED = "VISITOR_CREATED", "Visitor Created"
        VISITOR_UPDATED = "VISITOR_UPDATED", "Visitor Updated"
        VISITOR_BLACKLISTED = "VISITOR_BLACKLISTED", "Visitor Blacklisted"
        VISITOR_UNBLACKLISTED = "VISITOR_UNBLACKLISTED", "Visitor Unblacklisted"

        # User actions
        USER_CREATED = "USER_CREATED", "User Created"
        USER_UPDATED = "USER_UPDATED", "User Updated"
        USER_DEACTIVATED = "USER_DEACTIVATED", "User Deactivated"
        USER_LOGIN = "USER_LOGIN", "User Login"
        USER_LOGOUT = "USER_LOGOUT", "User Logout"

        # Organisation actions
        ORG_SETTINGS_UPDATED = "ORG_SETTINGS_UPDATED", "Organisation Settings Updated"
        EMERGENCY_LOCKDOWN_ACTIVATED = "EMERGENCY_LOCKDOWN_ACTIVATED", "Emergency Lockdown Activated"
        EMERGENCY_LOCKDOWN_DEACTIVATED = "EMERGENCY_LOCKDOWN_DEACTIVATED", "Emergency Lockdown Deactivated"

        # QR actions
        QR_GENERATED = "QR_GENERATED", "QR Generated"
        QR_SCANNED = "QR_SCANNED", "QR Scanned"
        QR_INVALID = "QR_INVALID", "QR Invalid"
        QR_EXPIRED = "QR_EXPIRED", "QR Expired"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    actor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs'
    )

    organisation = models.ForeignKey(
        Organisation,
        on_delete=models.CASCADE,
        related_name='audit_logs'
    )

    action = models.CharField(
        max_length=50,
        choices=Action.choices
    )

    # What was affected
    target_model = models.CharField(max_length=50, blank=True)
    target_id = models.CharField(max_length=100, blank=True)

    # Extra context
    details = models.JSONField(default=dict, blank=True)

    ip_address = models.GenericIPAddressField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.actor} → {self.action} ({self.created_at})"

    class Meta:
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=['organisation']),
            models.Index(fields=['action']),
            models.Index(fields=['actor']),
            models.Index(fields=['target_model', 'target_id']),
        ]