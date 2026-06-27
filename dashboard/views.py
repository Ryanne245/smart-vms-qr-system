from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from visits.models import Visit
from visitors.models import Visitor
from django.contrib.auth import get_user_model
from notifications.models import Notification
from organisations.models import Organisation
from visits.serializers import VisitSerializer
from visits.permissions import CanViewDashboard

User = get_user_model()


class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated, CanViewDashboard]

    def get(self, request):
        today = timezone.now().date()

        if request.user.role == "SUPER_ADMIN":
            return self.get_super_admin_stats(today)
        return self.get_org_admin_stats(request, today)

    def get_org_admin_stats(self, request, today):
        organisation = request.user.organisation

        # Visit stats
        total_visits_today = Visit.objects.filter(
            organisation=organisation,
            created_at__date=today
        ).count()

        total_visits_this_month = Visit.objects.filter(
            organisation=organisation,
            created_at__month=today.month,
            created_at__year=today.year
        ).count()

        active_visitors_now = Visit.objects.filter(
            organisation=organisation,
            status__in=[Visit.Status.CHECKED_IN, Visit.Status.OVERSTAY]
        ).count()

        pending_approvals = Visit.objects.filter(
            organisation=organisation,
            status=Visit.Status.PENDING
        ).count()

        overstay_count = Visit.objects.filter(
            organisation=organisation,
            status=Visit.Status.OVERSTAY
        ).count()

        rejected_today = Visit.objects.filter(
            organisation=organisation,
            status=Visit.Status.REJECTED,
            created_at__date=today
        ).count()

        expired_today = Visit.objects.filter(
            organisation=organisation,
            status=Visit.Status.EXPIRED,
            created_at__date=today
        ).count()

        checked_out_today = Visit.objects.filter(
            organisation=organisation,
            status=Visit.Status.CHECKED_OUT,
            created_at__date=today
        ).count()

        cancelled_today = Visit.objects.filter(
            organisation=organisation,
            status=Visit.Status.CANCELLED,
            created_at__date=today
        ).count()

        # Visitor stats
        total_visitors = Visitor.objects.filter(
            organisation=organisation
        ).count()

        blacklisted_visitors = Visitor.objects.filter(
            organisation=organisation,
            is_blacklisted=True
        ).count()

        # User stats
        total_users = User.objects.filter(
            organisation=organisation,
            is_active=True
        ).count()

        total_hosts = User.objects.filter(
            organisation=organisation,
            role="HOST",
            is_active=True
        ).count()

        total_security = User.objects.filter(
            organisation=organisation,
            role="SECURITY",
            is_active=True
        ).count()

        # Notification stats
        unread_notifications = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()

        # Recent visits
        recent_visits = Visit.objects.filter(
            organisation=organisation
        ).order_by('-created_at')[:5]

        return Response({
            "role": "ORG_ADMIN",
            "organisation": organisation.name,
            "emergency_lockdown": organisation.settings.emergency_lockdown,
            "generated_at": timezone.now(),
            "visits": {
                "total_today": total_visits_today,
                "total_this_month": total_visits_this_month,
                "active_now": active_visitors_now,
                "pending_approvals": pending_approvals,
                "overstay_count": overstay_count,
                "rejected_today": rejected_today,
                "expired_today": expired_today,
                "checked_out_today": checked_out_today,
                "cancelled_today": cancelled_today,
            },

            "visitors": {
                "total_registered": total_visitors,
                "blacklisted": blacklisted_visitors,
            },

            "users": {
                "total_active": total_users,
                "total_hosts": total_hosts,
                "total_security": total_security,
            },

            "notifications": {
                "unread_count": unread_notifications,
            },

            "recent_visits": VisitSerializer(recent_visits, many=True).data,
        }, status=status.HTTP_200_OK)

    def get_super_admin_stats(self, today):
        # Organisation stats
        total_organisations = Organisation.objects.count()
        active_organisations = Organisation.objects.filter(is_active=True).count()
        inactive_organisations = Organisation.objects.filter(is_active=False).count()
        organisations_on_lockdown = Organisation.objects.filter(
            settings__emergency_lockdown=True
        ).count()

        # Global visit stats
        total_visits_today = Visit.objects.filter(
            created_at__date=today
        ).count()

        total_visits_this_month = Visit.objects.filter(
            created_at__month=today.month,
            created_at__year=today.year
        ).count()

        active_visitors_now = Visit.objects.filter(
            status__in=[Visit.Status.CHECKED_IN, Visit.Status.OVERSTAY]
        ).count()

        pending_approvals = Visit.objects.filter(
            status=Visit.Status.PENDING
        ).count()

        overstay_count = Visit.objects.filter(
            status=Visit.Status.OVERSTAY
        ).count()

        checked_out_today = Visit.objects.filter(
            status=Visit.Status.CHECKED_OUT,
            created_at__date=today
        ).count()

        cancelled_today = Visit.objects.filter(
            status=Visit.Status.CANCELLED,
            created_at__date=today
        ).count()

        # Global user stats
        total_users = User.objects.filter(is_active=True).count()
        total_hosts = User.objects.filter(role="HOST", is_active=True).count()
        total_security = User.objects.filter(role="SECURITY", is_active=True).count()
        total_org_admins = User.objects.filter(role="ORG_ADMIN", is_active=True).count()

        # Global visitor stats
        total_visitors = Visitor.objects.count()
        blacklisted_visitors = Visitor.objects.filter(is_blacklisted=True).count()

        # Recent visits across all orgs
        recent_visits = Visit.objects.all().order_by('-created_at')[:10]

        return Response({
            "role": "SUPER_ADMIN",
            "generated_at": timezone.now(),

            "organisations": {
                "total": total_organisations,
                "active": active_organisations,
                "inactive": inactive_organisations,
                "on_lockdown": organisations_on_lockdown,
            },

            "visits": {
                "total_today": total_visits_today,
                "total_this_month": total_visits_this_month,
                "active_now": active_visitors_now,
                "pending_approvals": pending_approvals,
                "overstay_count": overstay_count,
                "checked_out_today": checked_out_today,
                "cancelled_today": cancelled_today,
            },

            "visitors": {
                "total_registered": total_visitors,
                "blacklisted": blacklisted_visitors,
            },
            "users": {
                "total_active": total_users,
                "total_hosts": total_hosts,
                "total_security": total_security,
                "total_org_admins": total_org_admins,
            },

            "recent_visits": VisitSerializer(recent_visits, many=True).data,
        }, status=status.HTTP_200_OK)


