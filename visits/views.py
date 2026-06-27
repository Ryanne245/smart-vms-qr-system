from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from .models import Visit
from .serializers import (
    VisitSerializer,
    VisitCreateSerializer,
    VisitApproveSerializer,
    VisitRejectSerializer,
    VisitCancelSerializer,
    VisitCheckOutSerializer,
    VisitOverstaySerializer,
    VisitExpireSerializer,
    QRScanSerializer,
    EvacuationSerializer,
)
from .permissions import (
    IsVisitInSameOrganisation,
    CanApproveOrRejectVisit,
    CanCancelVisit,
    CanCheckInVisit,
    CanCheckOutVisit,
    CanRegenerateQR,
    CanViewEvacuationList,
    CanViewActiveVisits,
    CanViewPendingVisits,
    CanViewQRCode,
    CanAddNotes,
    CanFlagOverstay,
)
from core.permissions import (
    IsSecurity,
    IsHost,
    IsOrgAdminOrSuperAdmin,
    IsSecurityOrOrgAdmin,
    IsHostOrOrgAdmin,
    IsSecurityOrOrgAdminOrHost,
    BelongsToOrganisation,
)
from core.utils import (
    create_audit_log,
    generate_qr_code,
    handle_host_approval_requirement,
    notify_visitor_of_approval,
    notify_visitor_of_rejection,
    notify_security_of_approval,
    notify_host_on_checkin,
    notify_checkout,
    notify_cancellation,
    notify_before_qr_expiry,
    check_and_expire_visit,
    check_and_flag_overstay,
)


class VisitListCreateView(APIView):

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated(), IsSecurity(), BelongsToOrganisation()]
        return [IsAuthenticated(), IsSecurityOrOrgAdminOrHost(), BelongsToOrganisation()]

    def get(self, request):
        organisation = request.user.organisation

        if request.user.role == "HOST":
            visits = Visit.objects.filter(
                host=request.user,
                organisation=organisation
            )
        elif request.user.role == "SECURITY":
            visits = Visit.objects.filter(
                organisation=organisation
            )
        else:
            visits = Visit.objects.filter(
                organisation=organisation
            )

        for visit in visits:
            check_and_expire_visit(visit)
            check_and_flag_overstay(visit)

        status_filter = request.query_params.get('status')
        if status_filter:
            visits = visits.filter(status=status_filter.upper())

        serializer = VisitSerializer(visits, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = VisitCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            visit = serializer.save()
            handle_host_approval_requirement(visit)
            create_audit_log(
                request=request,
                action="VISIT_CREATED",
                target_model="Visit",
                target_id=visit.id,
                details={
                    "visitor": f"{visit.visitor.first_name} {visit.visitor.last_name}",
                    "host": f"{visit.host.first_name} {visit.host.last_name}",
                }
            )
            return Response(
                VisitSerializer(visit).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VisitActiveView(APIView):
    permission_classes = [IsAuthenticated, CanViewActiveVisits, BelongsToOrganisation]

    def get(self, request):
        visits = Visit.objects.filter(
            organisation=request.user.organisation,
            status=Visit.Status.CHECKED_IN
        )
        for visit in visits:
            check_and_flag_overstay(visit)

        serializer = VisitSerializer(visits, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class VisitPendingView(APIView):
    permission_classes = [IsAuthenticated, CanViewPendingVisits, BelongsToOrganisation]
    def get(self, request):
        if request.user.role == "HOST":
            visits = Visit.objects.filter(
                host=request.user,
                organisation=request.user.organisation,
                status=Visit.Status.PENDING
            )
        else:
            visits = Visit.objects.filter(
                organisation=request.user.organisation,
                status=Visit.Status.PENDING
            )

        for visit in visits:
            check_and_expire_visit(visit)

        serializer = VisitSerializer(visits, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class VisitHistoryView(APIView):
    permission_classes = [IsAuthenticated, IsOrgAdminOrSuperAdmin, BelongsToOrganisation]

    def get(self, request):
        visits = Visit.objects.filter(
            organisation=request.user.organisation
        ).order_by('-created_at')

        status_filter = request.query_params.get('status')
        from_date = request.query_params.get('from_date')
        to_date = request.query_params.get('to_date')

        if status_filter:
            visits = visits.filter(status=status_filter.upper())
        if from_date:
            visits = visits.filter(created_at__gte=from_date)
        if to_date:
            visits = visits.filter(created_at__lte=to_date)

        serializer = VisitSerializer(visits, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class VisitMyVisitsView(APIView):
    permission_classes = [IsAuthenticated, IsHost, BelongsToOrganisation]

    def get(self, request):
        visits = Visit.objects.filter(
            host=request.user,
            organisation=request.user.organisation
        ).order_by('-created_at')

        for visit in visits:
            check_and_expire_visit(visit)
            check_and_flag_overstay(visit)

        serializer = VisitSerializer(visits, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class VisitRegisteredByMeView(APIView):
    permission_classes = [IsAuthenticated, IsSecurity, BelongsToOrganisation]

    def get(self, request):
        visits = Visit.objects.filter(
            registered_by=request.user,
            organisation=request.user.organisation
        ).order_by('-created_at')

        serializer = VisitSerializer(visits, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class VisitEvacuationView(APIView):
    permission_classes = [IsAuthenticated, CanViewEvacuationList, BelongsToOrganisation]

    def get(self, request):
        visits = Visit.objects.filter(
            organisation=request.user.organisation,
            status__in=[Visit.Status.CHECKED_IN, Visit.Status.OVERSTAY]
        )
        for visit in visits:
            check_and_flag_overstay(visit)

        serializer = EvacuationSerializer(visits, many=True)
        return Response({
            "total_inside": visits.count(),
            "visitors": serializer.data,
            "emergency_lockdown": request.user.organisation.settings.emergency_lockdown,
            "generated_at": timezone.now(),
        }, status=status.HTTP_200_OK)


class QRScanView(APIView):
    permission_classes = [IsAuthenticated, CanCheckInVisit, BelongsToOrganisation]

    def post(self, request):
        serializer = QRScanSerializer(data=request.data)
        if serializer.is_valid():
            visit = serializer.save(checked_in_by=request.user)
            notify_host_on_checkin(visit)
            notify_before_qr_expiry(visit)
            create_audit_log(
                request=request,
                action="QR_SCANNED",
                target_model="Visit",
                target_id=visit.id,
                details={
                    "visitor": f"{visit.visitor.first_name} {visit.visitor.last_name}",
                    "checked_in_at": str(visit.checked_in_at),
                }
            )
            return Response(
                VisitSerializer(visit).data,
                status=status.HTTP_200_OK
            )
        create_audit_log(
            request=request,
            action="QR_INVALID",
            target_model="Visit",
            target_id="unknown",
            details={"error": serializer.errors}
        )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VisitDetailView(APIView):
    permission_classes = [IsAuthenticated, IsVisitInSameOrganisation, BelongsToOrganisation]

    def get_object(self, request, visit_id):
        try:
            visit = Visit.objects.get(
                id=visit_id,
                organisation=request.user.organisation
            )
            return visit
        except Visit.DoesNotExist:
            return None

    def get(self, request, visit_id):
        visit = self.get_object(request, visit_id)
        if not visit:
            return Response(
                {"detail": "Visit not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        check_and_expire_visit(visit)
        check_and_flag_overstay(visit)
        serializer = VisitSerializer(visit)
        return Response(serializer.data, status=status.HTTP_200_OK)


class VisitQRView(APIView):
    permission_classes = [IsAuthenticated, CanViewQRCode, BelongsToOrganisation]

    def get(self, request, visit_id):
        try:
            visit = Visit.objects.get(
                id=visit_id,
                organisation=request.user.organisation
            )
        except Visit.DoesNotExist:
            return Response(
                {"detail": "Visit not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        if not visit.qr_code_image:
            return Response(
                {"detail": "QR code has not been generated yet."},
                status=status.HTTP_404_NOT_FOUND
            )

        notify_before_qr_expiry(visit)

        return Response({
            "qr_code_image": visit.qr_code_image,
            "qr_generated_at": visit.qr_generated_at,
            "qr_expires_at": visit.qr_expires_at,
            "is_valid": visit.is_qr_valid(),
        }, status=status.HTTP_200_OK)


class VisitQRRegenerateView(APIView):
    permission_classes = [IsAuthenticated, CanRegenerateQR, BelongsToOrganisation]

    def post(self, request, visit_id):
        try:
            visit = Visit.objects.get(
                id=visit_id,
                organisation=request.user.organisation
            )
        except Visit.DoesNotExist:
            return Response(
                {"detail": "Visit not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        if visit.status != Visit.Status.APPROVED:
            return Response(
                {"detail": "QR can only be regenerated for approved visits."},
                status=status.HTTP_400_BAD_REQUEST
            )

        visit = generate_qr_code(visit)
        notify_visitor_of_approval(visit)
        create_audit_log(
            request=request,
            action="QR_GENERATED",
            target_model="Visit",
            target_id=visit.id,
            details={"regenerated": True}
        )
        return Response({
            "detail": "QR code regenerated successfully.",
            "qr_code_image": visit.qr_code_image,
            "qr_expires_at": visit.qr_expires_at,
        }, status=status.HTTP_200_OK)


class VisitApproveView(APIView):
    permission_classes = [IsAuthenticated, CanApproveOrRejectVisit, BelongsToOrganisation]

    def post(self, request, visit_id):
        try:
            visit = Visit.objects.get(
                id=visit_id,
                organisation=request.user.organisation,
                host=request.user
            )
        except Visit.DoesNotExist:
            return Response(
                {"detail": "Visit not found."},
                status=status.HTTP_404_NOT_FOUND
            )
            visit = check_and_expire_visit(visit)
        if visit.status == Visit.Status.EXPIRED:
            return Response(
                {"detail": "This visit has expired and cannot be approved."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = VisitApproveSerializer()
        visit = serializer.save(visit=visit, approved_by=request.user)
        visit = generate_qr_code(visit)
        notify_visitor_of_approval(visit)
        notify_security_of_approval(visit)

        create_audit_log(
            request=request,
            action="VISIT_APPROVED",
            target_model="Visit",
            target_id=visit.id,
            details={
                "visitor": f"{visit.visitor.first_name} {visit.visitor.last_name}",
                "approved_by": request.user.email,
            }
        )
        return Response(
            VisitSerializer(visit).data,
            status=status.HTTP_200_OK
        )


class VisitRejectView(APIView):
    permission_classes = [IsAuthenticated, CanApproveOrRejectVisit, BelongsToOrganisation]

    def post(self, request, visit_id):
        try:
            visit = Visit.objects.get(
                id=visit_id,
                organisation=request.user.organisation,
                host=request.user
            )
        except Visit.DoesNotExist:
            return Response(
                {"detail": "Visit not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        visit = check_and_expire_visit(visit)
        if visit.status == Visit.Status.EXPIRED:
            return Response(
                {"detail": "This visit has already expired."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = VisitRejectSerializer(data=request.data)
        if serializer.is_valid():
            visit = serializer.save(visit=visit, rejected_by=request.user)
            notify_visitor_of_rejection(visit)
            create_audit_log(
                request=request,
                action="VISIT_REJECTED",
                target_model="Visit",
                target_id=visit.id,
                details={
                    "visitor": f"{visit.visitor.first_name} {visit.visitor.last_name}",
                    "reason": visit.rejection_reason,
                }
            )
            return Response(
                VisitSerializer(visit).data,
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VisitCancelView(APIView):
    permission_classes = [IsAuthenticated, CanCancelVisit, BelongsToOrganisation]

    def post(self, request, visit_id):
        try:
            visit = Visit.objects.get(
                id=visit_id,
                organisation=request.user.organisation
            )
        except Visit.DoesNotExist:
            return Response(
                {"detail": "Visit not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = VisitCancelSerializer(data=request.data)
        if serializer.is_valid():
            visit = serializer.save(visit=visit, cancelled_by=request.user)
            notify_cancellation(visit)
            create_audit_log(
                request=request,
                action="VISIT_CANCELLED",
                target_model="Visit",
                target_id=visit.id,
                details={
                    "cancelled_by": request.user.email,
                    "reason": visit.cancellation_reason,
                }
            )
            return Response(
                VisitSerializer(visit).data,
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VisitCheckOutView(APIView):
    permission_classes = [IsAuthenticated, CanCheckOutVisit, BelongsToOrganisation]
    def post(self, request, visit_id):
        try:
            visit = Visit.objects.get(
                id=visit_id,
                organisation=request.user.organisation,
                status__in=[Visit.Status.CHECKED_IN, Visit.Status.OVERSTAY]
            )
        except Visit.DoesNotExist:
            return Response(
                {"detail": "Visit not found or visitor is not checked in."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = VisitCheckOutSerializer()
        visit = serializer.save(visit=visit, checked_out_by=request.user)
        notify_checkout(visit)
        create_audit_log(
            request=request,
            action="VISIT_CHECKED_OUT",
            target_model="Visit",
            target_id=visit.id,
            details={
                "visitor": f"{visit.visitor.first_name} {visit.visitor.last_name}",
                "checked_out_at": str(visit.checked_out_at),
            }
        )
        return Response(
            VisitSerializer(visit).data,
            status=status.HTTP_200_OK
        )


class VisitNotesView(APIView):
    permission_classes = [IsAuthenticated, CanAddNotes, BelongsToOrganisation]

    def put(self, request, visit_id):
        try:
            visit = Visit.objects.get(
                id=visit_id,
                organisation=request.user.organisation
            )
        except Visit.DoesNotExist:
            return Response(
                {"detail": "Visit not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        notes = request.data.get('notes')
        if not notes:
            return Response(
                {"detail": "Notes field is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        visit.notes = notes
        visit.save(update_fields=['notes', 'updated_at'])
        create_audit_log(
            request=request,
            action="NOTES_ADDED",
            target_model="Visit",
            target_id=visit.id,
            details={"notes_added_by": request.user.email}
        )
        return Response(
            VisitSerializer(visit).data,
            status=status.HTTP_200_OK
        )