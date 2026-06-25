from django.db import models
import uuid
from django.contrib.auth import get_user_model
from organisations.models import Organisation

User = get_user_model()

class Visitor(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.EmailField(max_length=255)
    phone_number = models.CharField(max_length=20)

    organisation = models.ForeignKey(Organisation,
        on_delete=models.CASCADE,
        related_name='visitors'
    )

    is_active = models.BooleanField(default=True)

    # Blacklist fields
    is_blacklisted = models.BooleanField(default=False)
    blacklisted_at = models.DateTimeField(null=True, blank=True)
    blacklisted_reason = models.TextField(blank=True)
    blacklisted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='blacklisted_visitors')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    class Meta:
        verbose_name = "Visitor"
        verbose_name_plural = "Visitors"

        constraints = [
            models.UniqueConstraint(
                fields=['email', 'organisation'],
                name='unique_email_per_organisation'
            ),
            models.UniqueConstraint(
                fields=['phone_number', 'organisation'],
                name='unique_phone_per_organisation'
            )
        ]

        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['phone_number']),
        ]