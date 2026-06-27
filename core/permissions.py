from rest_framework.permissions import BasePermission


class IsSuperAdmin(BasePermission):
    """Only Super Admins can access"""
    message = "You must be a Super Admin to perform this action."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role == "SUPER_ADMIN"
        )


class IsOrgAdmin(BasePermission):
    """Only Org Admins can access"""
    message = "You must be an Organisation Admin to perform this action."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role == "ORG_ADMIN"
        )


class IsHost(BasePermission):
    """Only Hosts can access"""
    message = "You must be a Host to perform this action."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role == "HOST"
        )


class IsSecurity(BasePermission):
    """Only Security personnel can access"""
    message = "You must be a Security personnel to perform this action."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role == "SECURITY"
        )


class IsOrgAdminOrSuperAdmin(BasePermission):
    """Org Admins and Super Admins can access"""
    message = "You must be an Organisation Admin or Super Admin to perform this action."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role in ["ORG_ADMIN", "SUPER_ADMIN"]
        )


class IsSecurityOrOrgAdmin(BasePermission):
    """Security and Org Admins can access"""
    message = "You must be a Security personnel or Organisation Admin to perform this action."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role in ["SECURITY", "ORG_ADMIN"]
        )


class IsHostOrOrgAdmin(BasePermission):
    """Hosts and Org Admins can access"""
    message = "You must be a Host or Organisation Admin to perform this action."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role in ["HOST", "ORG_ADMIN"]
        )


class BelongsToOrganisation(BasePermission):
    """User must belong to an organisation"""
    message = "You must belong to an organisation to perform this action."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.organisation is not None
        )

class IsSecurityOrOrgAdminOrHost(BasePermission):
    """Security, Org Admin and Host can access"""
    message = "You do not have permission to perform this action."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role in ["SECURITY", "ORG_ADMIN", "HOST"]
        )


class CanAccessHosts(BasePermission):
    """Security and Org Admin can see hosts list"""
    message = "You do not have permission to view hosts."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role in ["SECURITY", "ORG_ADMIN"] and
            request.user.organisation is not None
        )