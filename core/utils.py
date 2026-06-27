import qrcode
import base64
from io import BytesIO
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from visits.models import Visit


def get_client_ip(request):
    """Extract client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def create_audit_log(request, action, target_model, target_id, details=None):
    """Create an audit log entry"""
    from auditlogs.models import AuditLog

    AuditLog.objects.create(
        actor=request.user if request.user.is_authenticated else None,
        organisation=request.user.organisation,
        action=action,
        target_model=target_model,
        target_id=str(target_id),
        details=details or {},
        ip_address=get_client_ip(request),
    )


def create_notification(recipient, notification_type, message, visit=None, organisation=None):
    """Create an in-app notification"""
    from notifications.models import Notification

    Notification.objects.create(
        recipient=recipient,
        visit=visit,
        organisation=organisation or recipient.organisation,
        notification_type=notification_type,
        channel=Notification.Channel.IN_APP,
        delivery_status=Notification.DeliveryStatus.SENT,
        message=message,
    )


def send_email_notification(recipient_email, subject, message, visit=None, recipient=None, organisation=None, notification_type=None):
    """Send email notification and log it"""
    from notifications.models import Notification

    notification = None

    if recipient:
        notification = Notification.objects.create(
            recipient=recipient,
            visit=visit,
            organisation=organisation or recipient.organisation,
            notification_type=notification_type or Notification.Type.VISIT_CREATED,
            channel=Notification.Channel.EMAIL,
            delivery_status=Notification.DeliveryStatus.PENDING,
            message=message,
        )

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            fail_silently=False,
        )
        if notification:
            notification.delivery_status = Notification.DeliveryStatus.SENT
            notification.save(update_fields=['delivery_status', 'updated_at'])

    except Exception as e:
        if notification:
            notification.delivery_status = Notification.DeliveryStatus.FAILED
            notification.failed_reason = str(e)
            notification.save(update_fields=['delivery_status', 'failed_reason', 'updated_at'])


def generate_qr_code(visit):
    """Generate QR code for a visit"""
    org_settings = visit.organisation.settings
    qr_expiry_minutes = org_settings.notify_before_expiry_minutes or 45

    qr = qrcode.make(str(visit.qr_code_token))
    buffer = BytesIO()
    qr.save(buffer, format='PNG')
    qr_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

    visit.qr_code_image = qr_base64
    visit.qr_generated_at = timezone.now()
    visit.qr_expires_at = timezone.now() + timezone.timedelta(minutes=qr_expiry_minutes)
    visit.save(update_fields=['qr_code_image', 'qr_generated_at', 'qr_expires_at', 'updated_at'])

    return visit


def handle_host_approval_requirement(visit):
    """Auto approve visit if org doesn't require host approval"""
    if not visit.organisation.settings.require_host_approval:
        visit.status = Visit.Status.APPROVED
        visit.host_responded_at = timezone.now()
        visit.save(update_fields=['status', 'host_responded_at', 'updated_at'])
        generate_qr_code(visit)
        notify_visitor_of_approval(visit)
        notify_security_of_approval(visit)
    else:
        notify_host_of_visit(visit)
    return visit
def check_and_expire_visit(visit):
    """Check if visit should be expired and expire it on demand"""
    from visits.models import Visit

    if visit.status != Visit.Status.PENDING:
        return visit

    org_settings = visit.organisation.settings
    expiry_minutes = org_settings.default_visit_duration or 60

    elapsed = (timezone.now() - visit.created_at).total_seconds() / 60

    if elapsed > expiry_minutes:
        visit.status = Visit.Status.EXPIRED
        visit.save(update_fields=['status', 'updated_at'])
        notify_visit_expiry(visit)

    return visit


def check_and_flag_overstay(visit):
    """Check if visitor is overstaying and flag it"""
    from visits.models import Visit

    if visit.status != Visit.Status.CHECKED_IN:
        return visit

    if not visit.is_overstaying():
        return visit

    org_settings = visit.organisation.settings
    grace_period = org_settings.overstay_grace_period_minutes or 5

    elapsed = (timezone.now() - visit.checked_in_at).total_seconds() / 60
    total_allowed = (visit.expected_duration or 60) + grace_period

    if elapsed > total_allowed:
        visit.status = Visit.Status.OVERSTAY
        visit.overstay_flagged = True
        visit.overstay_flagged_at = timezone.now()
        visit.save(update_fields=[
            'status',
            'overstay_flagged',
            'overstay_flagged_at',
            'updated_at'
        ])
        notify_overstay(visit)

    return visit


def check_and_unblacklist_visitor(visitor):
    """Auto unblacklist visitor if blacklist duration has passed"""
    if not visitor.is_blacklisted:
        return visitor

    if not visitor.blacklisted_at:
        return visitor

    org_settings = visitor.organisation.settings
    blacklist_days = org_settings.blacklist_duration_days or 7

    elapsed_days = (timezone.now() - visitor.blacklisted_at).days

    if elapsed_days >= blacklist_days:
        visitor.is_blacklisted = False
        visitor.blacklisted_at = None
        visitor.blacklisted_reason = ''
        visitor.blacklisted_by = None
        visitor.save(update_fields=[
            'is_blacklisted',
            'blacklisted_at',
            'blacklisted_reason',
            'blacklisted_by',
            'updated_at'
        ])

    return visitor


# ---- Notification functions ----

def notify_host_of_visit(visit):
    """Notify host when a new visit is created"""
    message = (
        f"You have a new visit request from "
        f"{visit.visitor.first_name} {visit.visitor.last_name}. "
        f"Purpose: {visit.purpose or 'Not specified'}. "
        f"Please approve or reject this visit."
    )
    create_notification(
        recipient=visit.host,
        notification_type="VISIT_CREATED",
        message=message,
        visit=visit,
    )
    send_email_notification(
        recipient_email=visit.host.email,
        subject="New Visit Request",
        message=message,
        visit=visit,
        recipient=visit.host,
        notification_type="VISIT_CREATED",
    )


def notify_visitor_of_approval(visit):
    """Notify visitor via email when visit is approved"""
    message = (
        f"Dear {visit.visitor.first_name}, your visit request has been approved. "
        f"Please present this QR code at the gate. "
        f"Your QR code expires at {visit.qr_expires_at.strftime('%Y-%m-%d %H:%M')}."
    )
    send_email_notification(
        recipient_email=visit.visitor.email,
        subject="Visit Approved - Your QR Code",
        message=message,
        visit=visit,
        notification_type="VISIT_APPROVED",
    )


def notify_visitor_of_rejection(visit):
    """Notify visitor via email when visit is rejected"""
    message = (
        f"Dear {visit.visitor.first_name}, your visit request has been rejected. "
        f"Reason: {visit.rejection_reason or 'Not specified'}."
    )
    send_email_notification(
        recipient_email=visit.visitor.email,
        subject="Visit Request Rejected",
        message=message,
        visit=visit,
        notification_type="VISIT_REJECTED",
    )

def notify_security_of_approval(visit):
    """Notify security when host approves a visit"""
    from user.models import User
    security_users = User.objects.filter(
        organisation=visit.organisation,
        role="SECURITY",
        is_active=True,
    )
    message = (
        f"Visit for {visit.visitor.first_name} {visit.visitor.last_name} "
        f"has been approved by {visit.host.first_name} {visit.host.last_name}. "
        f"Visitor may arrive soon."
    )
    for security in security_users:
        create_notification(
            recipient=security,
            notification_type="VISIT_APPROVED",
            message=message,
            visit=visit,
        )


def notify_host_on_checkin(visit):
    """Notify host when visitor checks in - respects org settings"""
    if not visit.organisation.settings.notify_host_on_checkin:
        return

    message = (
        f"Your visitor {visit.visitor.first_name} {visit.visitor.last_name} "
        f"has checked in at {visit.checked_in_at.strftime('%Y-%m-%d %H:%M')}."
    )
    create_notification(
        recipient=visit.host,
        notification_type="VISITOR_CHECKED_IN",
        message=message,
        visit=visit,
    )


def notify_checkout(visit):
    """Notify host when visitor checks out"""
    duration = int(
        (visit.checked_out_at - visit.checked_in_at).total_seconds() / 60
    )
    message = (
        f"Your visitor {visit.visitor.first_name} {visit.visitor.last_name} "
        f"has checked out at {visit.checked_out_at.strftime('%Y-%m-%d %H:%M')}. "
        f"Visit duration: {duration} minutes."
    )
    create_notification(
        recipient=visit.host,
        notification_type="VISITOR_CHECKED_OUT",
        message=message,
        visit=visit,
    )


def notify_overstay(visit):
    """Notify host and security when visitor overstays"""
    from user.models import User
    message = (
        f"Visitor {visit.visitor.first_name} {visit.visitor.last_name} "
        f"has exceeded their expected visit duration. "
        f"Please take appropriate action."
    )
    create_notification(
        recipient=visit.host,
        notification_type="VISIT_OVERSTAY",
        message=message,
        visit=visit,
    )
    send_email_notification(
        recipient_email=visit.host.email,
        subject="Visitor Overstay Alert",
        message=message,
        visit=visit,
        recipient=visit.host,
        notification_type="VISIT_OVERSTAY",
    )
    security_users = User.objects.filter(
        organisation=visit.organisation,
        role="SECURITY",
        is_active=True,
    )
    for security in security_users:
        create_notification(
            recipient=security,
            notification_type="VISIT_OVERSTAY",
            message=message,
            visit=visit,
        )


def notify_visit_expiry(visit):
    """Notify security when visit expires"""
    from user.models import User
    message = (
        f"Visit for {visit.visitor.first_name} {visit.visitor.last_name} "
        f"has expired. Host did not respond in time."
    )
    security_users = User.objects.filter(
        organisation=visit.organisation,
        role="SECURITY",
        is_active=True,
    )
    for security in security_users:
        create_notification(
            recipient=security,
            notification_type="VISIT_EXPIRED",
            message=message,
            visit=visit,
        )


def notify_cancellation(visit):
    """Notify relevant parties when visit is cancelled"""
    message = (
        f"Visit for {visit.visitor.first_name} {visit.visitor.last_name} "
        f"has been cancelled. "
        f"Reason: {visit.cancellation_reason or 'Not specified'}."
    )
    if visit.cancelled_by != visit.host:
        create_notification(
            recipient=visit.host,
            notification_type="VISIT_CANCELLED",
            message=message,
            visit=visit,
        )
    send_email_notification(
        recipient_email=visit.visitor.email,
        subject="Visit Cancelled",
        message=message,
        visit=visit,
        notification_type="VISIT_CANCELLED",
    )


def notify_blacklist(visitor, blacklisted_by):
    """Notify org admins when visitor is blacklisted"""
    from user.models import User
    message = (
        f"Visitor {visitor.first_name} {visitor.last_name} "
        f"has been blacklisted by {blacklisted_by.first_name} {blacklisted_by.last_name}. "
        f"Reason: {visitor.blacklisted_reason or 'Not specified'}."
    )
    org_admins = User.objects.filter(
        organisation=visitor.organisation,
        role="ORG_ADMIN",
        is_active=True,
    )
    for admin in org_admins:
        create_notification(
            recipient=admin,
            notification_type="VISITOR_BLACKLISTED",
            message=message,
        )


def notify_before_qr_expiry(visit):
    """Notify security before QR expires"""
    from user.models import User

    if not visit.qr_expires_at:
        return

    org_settings = visit.organisation.settings
    notify_minutes = org_settings.notify_before_expiry_minutes or 15

    time_until_expiry = (visit.qr_expires_at - timezone.now()).total_seconds() / 60

    if time_until_expiry <= notify_minutes:
        message = (
            f"QR code for {visit.visitor.first_name} {visit.visitor.last_name} "
            f"will expire in {int(time_until_expiry)} minutes."
        )
        security_users = User.objects.filter(
            organisation=visit.organisation,
            role="SECURITY",
            is_active=True,
        )
        for security in security_users:
            create_notification(
                recipient=security,
                notification_type="VISIT_EXPIRED",
                message=message,
                visit=visit,
            )