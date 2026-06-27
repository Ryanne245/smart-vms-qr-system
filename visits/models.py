import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


class Visit(models.Model):

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        CHECKED_IN = "CHECKED_IN", "Checked In"
        CHECKED_OUT = "CHECKED_OUT", "Checked Out"
        EXPIRED = "EXPIRED", "Expired"
        CANCELLED = "CANCELLED", "Cancelled"
        OVERSTAY = "OVERSTAY", "Overstay"

    VALID_TRANSITIONS = {
        Status.PENDING: [Status.APPROVED, Status.REJECTED, Status.EXPIRED, Status.CANCELLED],
        Status.APPROVED: [Status.CHECKED_IN, Status.EXPIRED, Status.CANCELLED],
        Status.CHECKED_IN: [Status.CHECKED_OUT, Status.OVERSTAY],
        Status.OVERSTAY: [Status.CHECKED_OUT],
        Status.CHECKED_OUT: [],
        Status.REJECTED: [],
        Status.EXPIRED: [],
        Status.CANCELLED: [],
    }

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    visitor = models.ForeignKey(
        'visitors.Visitor',
        on_delete=models.CASCADE,
        related_name='visits'
    )

    host = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='hosted_visits'
    )

    registered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='registered_visits'
    )

    organisation = models.ForeignKey(
        'organisations.Organisation',
        on_delete=models.CASCADE,
        related_name='visits'
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )

    purpose = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    # QR fields
    qr_code_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    qr_code_image = models.TextField(blank=True)
    qr_generated_at = models.DateTimeField(null=True, blank=True)
    qr_expires_at = models.DateTimeField(null=True, blank=True)

    # Timing fields
    expected_duration = models.IntegerField(null=True, blank=True)  # in minutes
    scheduled_time = models.DateTimeField(null=True, blank=True)
    checked_in_at = models.DateTimeField(null=True, blank=True)
    checked_out_at = models.DateTimeField(null=True, blank=True)
    host_responded_at = models.DateTimeField(null=True, blank=True)

    # Check in/out tracking
    checked_in_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='checkins_performed'
    )

    checked_out_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='checkouts_performed'
    )

    # Cancellation tracking
    cancelled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cancelled_visits'
    )
    cancellation_reason = models.TextField(blank=True)

    # Rejection tracking
    rejection_reason = models.TextField(blank=True)

    # Overstay
    overstay_flagged = models.BooleanField(default=False)
    overstay_flagged_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.visitor} visiting {self.host} - {self.status}"

    def is_qr_valid(self):
        if not self.qr_expires_at:
            return False
        return timezone.now() < self.qr_expires_at and self.status == self.Status.APPROVED

    def is_overstaying(self):
        if self.status != self.Status.CHECKED_IN:
            return False
        if not self.checked_in_at or not self.expected_duration:
            return False
        elapsed = (timezone.now() - self.checked_in_at).total_seconds() / 60
        return elapsed > self.expected_duration
    
    def can_transition_to(self, new_status):
        return new_status in self.VALID_TRANSITIONS.get(self.status, [])

    class Meta:
        verbose_name = "Visit"
        verbose_name_plural = "Visits"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['organisation']),
            models.Index(fields=['scheduled_time']),
            models.Index(fields=['qr_code_token']),
        ]