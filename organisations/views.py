from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .models import Organisation, OrganisationSettings
from .serializers import (
    OrganisationSerializer,
    OrganisationDetailSerializer,
    OrganisationSettingsSerializer,
)
from core.permissions import (
    IsSuperAdmin,
    IsOrgAdmin,
    IsOrgAdminOrSuperAdmin,
    BelongsToOrganisation,
)
from core.utils import create_audit_log


class OrganisationListCreateView(APIView):
    
    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated(), IsSuperAdmin()]
        return [IsAuthenticated(), IsOrgAdminOrSuperAdmin()]

    def get(self, request):
        if request.user.role == "SUPER_ADMIN":
            organisations = Organisation.objects.all()
        else:
            organisations = Organisation.objects.filter(
                id=request.user.organisation.id
            )
        serializer = OrganisationSerializer(organisations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = OrganisationSerializer(data=request.data)
        if serializer.is_valid():
            organisation = serializer.save()
            # Auto create settings for new org
            OrganisationSettings.objects.create(organisation=organisation)
            create_audit_log(
                request=request,
                action="ORG_SETTINGS_UPDATED",
                target_model="Organisation",
                target_id=organisation.id,
                details={"name": organisation.name}
            )
            return Response(
                OrganisationSerializer(organisation).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrganisationMineView(APIView):
    permission_classes = [IsAuthenticated, BelongsToOrganisation]

    def get(self, request):
        organisation = request.user.organisation
        serializer = OrganisationDetailSerializer(organisation)
        return Response(serializer.data, status=status.HTTP_200_OK)


class OrganisationDetailView(APIView):
    permission_classes = [IsAuthenticated, IsOrgAdminOrSuperAdmin]

    def get_object(self, request, org_id):
        try:
            if request.user.role == "SUPER_ADMIN":
                return Organisation.objects.get(id=org_id)
            return Organisation.objects.get(
                id=org_id,
                id=request.user.organisation.id
            )
        except Organisation.DoesNotExist:
            return None

    def get(self, request, org_id):
        organisation = self.get_object(request, org_id)
        if not organisation:
            return Response(
                {"detail": "Organisation not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = OrganisationDetailSerializer(organisation)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, org_id):
        organisation = self.get_object(request, org_id)
        if not organisation:
            return Response(
                {"detail": "Organisation not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = OrganisationSerializer(
            organisation,
            data=request.data,
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            create_audit_log(
                request=request,
                action="ORG_SETTINGS_UPDATED",
                target_model="Organisation",
                target_id=organisation.id,
                details={"updated_fields": list(request.data.keys())}
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class OrganisationDeactivateView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def put(self, request, org_id):
        try:
            organisation = Organisation.objects.get(id=org_id)
        except Organisation.DoesNotExist:
            return Response(
                {"detail": "Organisation not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        organisation.is_active = False
        organisation.save(update_fields=['is_active'])
        create_audit_log(
            request=request,
            action="ORG_SETTINGS_UPDATED",
            target_model="Organisation",
            target_id=organisation.id,
            details={"action": "deactivated"}
        )
        return Response(
            {"detail": "Organisation deactivated successfully."},
            status=status.HTTP_200_OK
        )


class OrganisationSettingsView(APIView):

    def get_permissions(self):
        if self.request.method == 'PUT':
            return [IsAuthenticated(), IsOrgAdmin()]
        return [IsAuthenticated(), IsOrgAdminOrSuperAdmin()]

    def get_object(self, request, org_id):
        try:
            if request.user.role == "SUPER_ADMIN":
                organisation = Organisation.objects.get(id=org_id)
            else:
                organisation = Organisation.objects.get(
                    id=org_id,
                    id=request.user.organisation.id
                )
            return organisation.settings
        except (Organisation.DoesNotExist, OrganisationSettings.DoesNotExist):
            return None

    def get(self, request, org_id):
        settings = self.get_object(request, org_id)
        if not settings:
            return Response(
                {"detail": "Settings not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = OrganisationSettingsSerializer(settings)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, org_id):
        settings = self.get_object(request, org_id)
        if not settings:
            return Response(
                {"detail": "Settings not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = OrganisationSettingsSerializer(
            settings,
            data=request.data,
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            create_audit_log(
                request=request,
                action="ORG_SETTINGS_UPDATED",
                target_model="OrganisationSettings",
                target_id=settings.id,
                details={"updated_fields": list(request.data.keys())}
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrganisationLockdownView(APIView):
    permission_classes = [IsAuthenticated, IsOrgAdmin, BelongsToOrganisation]

    def post(self, request, org_id):
        try:
            organisation = Organisation.objects.get(
                id=org_id,
                id=request.user.organisation.id
            )
        except Organisation.DoesNotExist:
            return Response(
                {"detail": "Organisation not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        settings = organisation.settings
        # Toggle lockdown
        settings.emergency_lockdown = not settings.emergency_lockdown
        settings.save(update_fields=['emergency_lockdown'])

        action = "EMERGENCY_LOCKDOWN_ACTIVATED" if settings.emergency_lockdown else "EMERGENCY_LOCKDOWN_DEACTIVATED"
        status_message = "activated" if settings.emergency_lockdown else "deactivated"

        create_audit_log(
            request=request,
            action=action,
            target_model="OrganisationSettings",
            target_id=settings.id,
            details={"lockdown": settings.emergency_lockdown}
        )

        return Response(
            {"detail": f"Emergency lockdown {status_message} successfully."},
            status=status.HTTP_200_OK
        )