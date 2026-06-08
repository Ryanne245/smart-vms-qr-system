from django.db import models

# Create your models here.
class Organisation(models.Model):
    name= models.CharField(max_length=255)
    address= models.TextField()
    email = models.EmailField(max_length=255, unique=True)
    phone_number =  models.CharField(max_length=20, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__ (self):
        return self.name
    class Meta:
        verbose_name = "Organisation"
        verbose_name_plural = "Organisations"


class OrganisationSettings(models.Model):
    organisation = models.OneToOneField(Organisation, on_delete=models.CASCADE, related_name='settings')
    default_visit_duration = models.IntegerField(default=60)   # in minutes
    require_host_approval = models.BooleanField(default=True)
    notify_host_on_checkin = models.BooleanField(default=True)
    allow_multiple_active_visits = models.BooleanField(default=False)
    notify_before_expiry_minutes = models.IntegerField(default=15)
    overstay_grace_period_minutes = models.IntegerField(default=5)
    emergency_lockdown = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Settings for {self.organisation.name}"
    
    class Meta:
        verbose_name = "Organisation Setting"
        verbose_name_plural = "Organisation Settings"
