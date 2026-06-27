from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .models import AuditLog
from .serializers import (
    AuditLogSerializer,
    AuditLogMiniSerializer,
    AuditLogFilterSerializer,
)
from core.permissions import (
    IsOrgAdminOrSuperAdmin,
    BelongsToOrganisation,
)


class AuditLogListView(APIView):
    permission_classes = [IsAuthenticated, IsOrgAdminOrSuperAdmin, BelongsToOrganisation]

    def get(self, request):
        if request.user.role == "SUPER_ADMIN":
            logs = AuditLog.objects.all()
        else:
            logs = AuditLog.objects.filter(
                organisation=request.user.organisation
            )

        filter_serializer = AuditLogFilterSerializer(data=request.query_params)
        if filter_serializer.is_valid():
            action = filter_serializer.validated_data.get('action')
            target_model = filter_serializer.validated_data.get('target_model')
            target_id = filter_serializer.validated_data.get('target_id')
            from_date = filter_serializer.validated_data.get('from_date')
            to_date = filter_serializer.validated_data.get('to_date')
            actor_email = filter_serializer.validated_data.get('actor_email')

            if action:
                logs = logs.filter(action=action)
            if target_model:
                logs = logs.filter(target_model=target_model)
            if target_id:
                logs = logs.filter(target_id=target_id)
            if from_date:
                logs = logs.filter(created_at__gte=from_date)
            if to_date:
                logs = logs.filter(created_at__lte=to_date)
            if actor_email:
                logs = logs.filter(actoremailicontains=actor_email)

        logs = logs.order_by('-created_at')
        serializer = AuditLogMiniSerializer(logs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AuditLogDetailView(APIView):
    permission_classes = [IsAuthenticated, IsOrgAdminOrSuperAdmin, BelongsToOrganisation]

    def get(self, request, log_id):
        try:
            if request.user.role == "SUPER_ADMIN":
                log = AuditLog.objects.get(id=log_id)
            else:
                log = AuditLog.objects.get(
                    id=log_id,
                    organisation=request.user.organisation
                )
        except AuditLog.DoesNotExist:
            return Response(
                {"detail": "Audit log not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = AuditLogSerializer(log)
        return Response(serializer.data, status=status.HTTP_200_OK)