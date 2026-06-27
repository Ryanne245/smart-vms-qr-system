from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q

from .models import Visitor
from .serializers import (
    VisitorSerializer,
    VisitorCreateSerializer,
    VisitorUpdateSerializer,
    BlacklistVisitorSerializer,
    VisitorMiniSerializer,
    VisitorSearchSerializer,
)
from core.permissions import (
    IsSecurity,
    IsOrgAdmin,
    IsSecurityOrOrgAdmin,
    BelongsToOrganisation,
)
from core.utils import (
    create_audit_log,
    create_notification,
    notify_blacklist,
    check_and_unblacklist_visitor,
)
from visits.models import Visit
from visits.serializers import VisitSerializer


class VisitorListCreateView(APIView):

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated(), IsSecurity(), BelongsToOrganisation()]
        return [IsAuthenticated(), IsSecurityOrOrgAdmin(), BelongsToOrganisation()]

    def get(self, request):
        visitors = Visitor.objects.filter(
            organisation=request.user.organisation
        )

        # Check and auto unblacklist expired blacklists
        for visitor in visitors:
            check_and_unblacklist_visitor(visitor)

        is_blacklisted = request.query_params.get('is_blacklisted')
        is_active = request.query_params.get('is_active')

        if is_blacklisted is not None:
            visitors = visitors.filter(is_blacklisted=is_blacklisted.lower() == 'true')
        if is_active is not None:
            visitors = visitors.filter(is_active=is_active.lower() == 'true')

        serializer = VisitorSerializer(visitors, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = VisitorCreateSerializer(data=request.data)
        if serializer.is_valid():
            # Check if visitor already exists in this org
            email = serializer.validated_data.get('email')
            phone = serializer.validated_data.get('phone_number')
            organisation = request.user.organisation

            existing_visitor = Visitor.objects.filter(
                Q(email=email) | Q(phone_number=phone),
                organisation=organisation
            ).first()

            if existing_visitor:
                # Returning visitor - just return existing record
                check_and_unblacklist_visitor(existing_visitor)
                if existing_visitor.is_blacklisted:
                    return Response(
                        {"detail": "This visitor is blacklisted and cannot be registered."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                return Response(
                    VisitorSerializer(existing_visitor).data,
                    status=status.HTTP_200_OK
                )

            # New visitor
            visitor = serializer.save(organisation=organisation)
            create_audit_log(
                request=request,
                action="VISITOR_CREATED",
                target_model="Visitor",
                target_id=visitor.id,
                details={"name": f"{visitor.first_name} {visitor.last_name}"}
            )
            return Response(
                VisitorSerializer(visitor).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VisitorSearchView(APIView):
    permission_classes = [IsAuthenticated, IsSecurity, BelongsToOrganisation]

    def get(self, request):
        serializer = VisitorSearchSerializer(data=request.query_params)
        if serializer.is_valid():
            query = serializer.validated_data['query']
            visitors = Visitor.objects.filter(
                organisation=request.user.organisation,
                is_active=True,
            ).filter(
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(email__icontains=query) |
                Q(phone_number__icontains=query)
            )
            serializer = VisitorMiniSerializer(visitors, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VisitorDetailView(APIView):
    permission_classes = [IsAuthenticated, IsSecurityOrOrgAdmin, BelongsToOrganisation]

    def get_object(self, request, visitor_id):
        try:
            return Visitor.objects.get(
                id=visitor_id,
                organisation=request.user.organisation
            )
        except Visitor.DoesNotExist:
            return None

    def get(self, request, visitor_id):
        visitor = self.get_object(request, visitor_id)
        if not visitor:
            return Response(
                {"detail": "Visitor not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        check_and_unblacklist_visitor(visitor)
        serializer = VisitorSerializer(visitor)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, visitor_id):
        visitor = self.get_object(request, visitor_id)
        if not visitor:
            return Response(
                {"detail": "Visitor not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = VisitorUpdateSerializer(
            visitor,
            data=request.data,
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            create_audit_log(
                request=request,
                action="VISITOR_UPDATED",
                target_model="Visitor",
                target_id=visitor.id,
                details={"updated_fields": list(request.data.keys())}
            )
            return Response(
                VisitorSerializer(visitor).data,
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VisitorBlacklistView(APIView):
    permission_classes = [IsAuthenticated, IsOrgAdmin, BelongsToOrganisation]

    def post(self, request, visitor_id):
        try:
            visitor = Visitor.objects.get(
                id=visitor_id,
                organisation=request.user.organisation
            )
        except Visitor.DoesNotExist:
            return Response(
                {"detail": "Visitor not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        if visitor.is_blacklisted:
            return Response(
                {"detail": "Visitor is already blacklisted."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = BlacklistVisitorSerializer(data=request.data)
        if serializer.is_valid():
            from django.utils import timezone
            visitor.is_blacklisted = True
            visitor.blacklisted_at = timezone.now()
            visitor.blacklisted_reason = serializer.validated_data['blacklisted_reason']
            visitor.blacklisted_by = request.user
            visitor.save(update_fields=[
                'is_blacklisted',
                'blacklisted_at',
                'blacklisted_reason',
                'blacklisted_by',
                'updated_at'
            ])
            notify_blacklist(visitor, request.user)
            create_audit_log(
                request=request,
                action="VISITOR_BLACKLISTED",
                target_model="Visitor",
                target_id=visitor.id,
                details={"reason": visitor.blacklisted_reason}
            )
            return Response(
                {"detail": "Visitor blacklisted successfully."},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VisitorUnblacklistView(APIView):
    permission_classes = [IsAuthenticated, IsOrgAdmin, BelongsToOrganisation]

    def post(self, request, visitor_id):
        try:
            visitor = Visitor.objects.get(
                id=visitor_id,
                organisation=request.user.organisation
            )
        except Visitor.DoesNotExist:
            return Response(
                {"detail": "Visitor not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        if not visitor.is_blacklisted:
            return Response(
                {"detail": "Visitor is not blacklisted."},
                status=status.HTTP_400_BAD_REQUEST
            )

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
        create_audit_log(
            request=request,
            action="VISITOR_UNBLACKLISTED",
            target_model="Visitor",
            target_id=visitor.id,
            details={"unblacklisted_by": request.user.email}
        )
        return Response(
            {"detail": "Visitor unblacklisted successfully."},
            status=status.HTTP_200_OK
        )


class VisitorVisitHistoryView(APIView):
    permission_classes = [IsAuthenticated, IsSecurityOrOrgAdmin, BelongsToOrganisation]

    def get(self, request, visitor_id):
        try:
            visitor = Visitor.objects.get(
                id=visitor_id,
                organisation=request.user.organisation
            )
        except Visitor.DoesNotExist:
            return Response(
                {"detail": "Visitor not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        visits = Visit.objects.filter(
            visitor=visitor,
            organisation=request.user.organisation
        ).order_by('-created_at')

        serializer = VisitSerializer(visits, many=True)
        return Response({
            "visitor": VisitorSerializer(visitor).data,
            "visits": serializer.data
        }, status=status.HTTP_200_OK)