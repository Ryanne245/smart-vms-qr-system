from rest_framework.permissions import BasePermission


class IsVisitInSameOrganisation(BasePermission):
    """Check if the visit belongs to the same organisation as the logged in user"""
    message = "You do not have permission to access this visit."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.organisation is not None
        )

    def has_object_permission(self, request, view, obj):
        return obj.organisation == request.user.organisation


class IsVisitHost(BasePermission):
    """Check if the logged in user is the host of this specific visit"""
    message = "You must be the host of this visit to perform this action."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role == "HOST"
        )

    def has_object_permission(self, request, view, obj):
        return obj.host == request.user


class IsVisitRegisteredBy(BasePermission):
    """Check if the logged in user registered this specific visit"""
    message = "You must be the security personnel who registered this visit to perform this action."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role == "SECURITY"
        )

    def has_object_permission(self, request, view, obj):
        return obj.registered_by == request.user


class CanCancelVisit(BasePermission):
    """Host, security who registered, or org admin can cancel"""
    message = "You must be the host or the security who registered this visit to cancel it."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role in ["HOST", "SECURITY", "ORG_ADMIN"]
        )

    def has_object_permission(self, request, view, obj):
        return (
            obj.host == request.user or
            obj.registered_by == request.user or
            request.user.role == "ORG_ADMIN"
        )


class CanApproveOrRejectVisit(BasePermission):
    """Only the specific host of this visit can approve or reject"""
    message = "Only the host of this visit can approve or reject it."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role == "HOST"
        )

    def has_object_permission(self, request, view, obj):
        return obj.host == request.user


class CanCheckInVisit(BasePermission):
    """Only security from the same organisation can check in a visitor"""
    message = "Only security personnel can check in visitors."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role == "SECURITY" and
            request.user.organisation is not None
        )

    def has_object_permission(self, request, view, obj):
        return obj.organisation == request.user.organisation


class CanCheckOutVisit(BasePermission):
    """Only security from the same organisation can check out a visitor"""
    message = "Only security personnel can check out visitors."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role == "SECURITY" and
            request.user.organisation is not None
        )

    def has_object_permission(self, request, view, obj):
        return obj.organisation == request.user.organisation


class CanRegenerateQR(BasePermission):
    """Only the host or security from same org can regenerate QR"""
    message = "You do not have permission to regenerate this QR code."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role in ["HOST", "SECURITY", "ORG_ADMIN"]
        )
    
    def has_object_permission(self, request, view, obj):
        return (
            obj.host == request.user or
            obj.organisation == request.user.organisation
        )


class CanViewEvacuationList(BasePermission):
    """Only security and org admin from same organisation can view evacuation list"""
    message = "You do not have permission to view the evacuation list."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role in ["SECURITY", "ORG_ADMIN"] and
            request.user.organisation is not None
        )


class CanViewDashboard(BasePermission):
    """ORG_ADMIN sees their org stats, SUPER_ADMIN sees global stats"""
    message = "You do not have permission to view the dashboard."

    def has_permission(self, request, view):
        if request.user.is_authenticated and request.user.role == "SUPER_ADMIN":
            return True
        return (
            request.user.is_authenticated and
            request.user.role == "ORG_ADMIN" and
            request.user.organisation is not None
        )


class CanFlagOverstay(BasePermission):
    """Only security and org admin can flag overstay"""
    message = "You do not have permission to flag overstay."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role in ["SECURITY", "ORG_ADMIN"] and
            request.user.organisation is not None
        )

    def has_object_permission(self, request, view, obj):
        return obj.organisation == request.user.organisation


class CanViewActiveVisits(BasePermission):
    """Security and Org Admin can view active visits"""
    message = "You do not have permission to view active visits."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role in ["SECURITY", "ORG_ADMIN"] and
            request.user.organisation is not None
        )


class CanViewPendingVisits(BasePermission):
    """Host and Org Admin can view pending visits"""
    message = "You do not have permission to view pending visits."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role in ["HOST", "ORG_ADMIN"] and
            request.user.organisation is not None
        )


class CanViewQRCode(BasePermission):
    """Host and Security can view QR code"""
    message = "You do not have permission to view this QR code."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role in ["HOST", "SECURITY", "ORG_ADMIN"]
        )

    def has_object_permission(self, request, view, obj):
        return (
            obj.host == request.user or
            obj.organisation == request.user.organisation
        )


class CanAddNotes(BasePermission):
    """Only security from same org can add notes to a visit"""
    message = "Only security personnel can add notes to a visit."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role in ["SECURITY", "ORG_ADMIN"] and
            request.user.organisation is not None
        )

    def has_object_permission(self, request, view, obj):
        return obj.organisation == request.user.organisations