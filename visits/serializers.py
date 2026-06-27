from rest_framework import serializers
from django.utils import timezone
from .models import Visit
from visitors.serializers import VisitorMiniSerializer
from user.serializers import UserMiniSerializer


class VisitSerializer(serializers.ModelSerializer):
    """Full visit info - used for detailed view"""
    visitor = VisitorMiniSerializer(read_only=True)
    host = UserMiniSerializer(read_only=True)
    registered_by = UserMiniSerializer(read_only=True)
    checked_in_by = UserMiniSerializer(read_only=True)
    checked_out_by = UserMiniSerializer(read_only=True)
    cancelled_by = UserMiniSerializer(read_only=True)

    class Meta:
        model = Visit
        fields = [
            'id',
            'visitor',
            'host',
            'registered_by',
            'organisation',
            'status',
            'purpose',
            'notes',
            'qr_code_image',
            'qr_generated_at',
            'qr_expires_at',
            'expected_duration',
            'scheduled_time',
            'checked_in_at',
            'checked_out_at',
            'host_responded_at',
            'checked_in_by',
            'checked_out_by',
            'cancelled_by',
            'cancellation_reason',
            'rejection_reason',
            'overstay_flagged',
            'overstay_flagged_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'organisation',
            'status',
            'qr_code_image',
            'qr_code_token',
            'qr_generated_at',
            'qr_expires_at',
            'checked_in_at',
            'checked_out_at',
            'host_responded_at',
            'checked_in_by',
            'checked_out_by',
            'cancelled_by',
            'overstay_flagged',
            'overstay_flagged_at',
            'created_at',
            'updated_at',
        ]


class VisitCreateSerializer(serializers.ModelSerializer):
    """Used by security to create a visit"""
    class Meta:
        model = Visit
        fields = [
            'id',
            'visitor',
            'host',
            'purpose',
            'scheduled_time',
        ]
        read_only_fields = ['id']

    def validate(self, attrs):
        request = self.context.get('request')
        organisation = request.user.organisation

        # Check emergency lockdown
        settings = organisation.settings
        if settings.emergency_lockdown:
            raise serializers.ValidationError({
                "detail": "System is under emergency lockdown. No visits can be created."
            })

        # Check visitor belongs to this org
        visitor = attrs.get('visitor')
        if visitor.organisation != organisation:
            raise serializers.ValidationError({
                "visitor": "Visitor does not belong to this organisation."
            })

        # Check visitor is not blacklisted
        if visitor.is_blacklisted:
            raise serializers.ValidationError({
                "visitor": "This visitor is blacklisted and cannot be registered."
            })

        # Check host belongs to this org and is a HOST
        host = attrs.get('host')
        if host.organisation != organisation:
            raise serializers.ValidationError({
                "host": "Host does not belong to this organisation."
            })
        if host.role != 'HOST':
            raise serializers.ValidationError({
                "host": "Selected user is not a host."
            })

        # Check multiple active visits
        if not settings.allow_multiple_active_visits:
            active_visit = Visit.objects.filter(
                visitor=visitor,
                organisation=organisation,
                status__in=[
                    Visit.Status.PENDING,
                    Visit.Status.APPROVED,
                    Visit.Status.CHECKED_IN
                ]
            ).exists()
            if active_visit:
                raise serializers.ValidationError({
                    "visitor": "This visitor already has an active visit."
                })

        return attrs

    def create(self, validated_data):
        request = self.context.get('request')
        organisation = request.user.organisation
        settings = organisation.settings

        visit = Visit.objects.create(
            **validated_data,
            organisation=organisation,
            registered_by=request.user,
            expected_duration=settings.default_visit_duration,
        )
        return visit


class VisitApproveSerializer(serializers.Serializer):
    """Used by host to approve a visit"""
    def save(self, visit, approved_by):
        if not visit.can_transition_to(Visit.Status.APPROVED):
            raise serializers.ValidationError({
                "detail": "This visit cannot be approved in its current state."
            })
        visit.status = Visit.Status.APPROVED
        visit.host_responded_at = timezone.now()
        visit.save(update_fields=['status', 'host_responded_at', 'updated_at'])
        return visit


class VisitRejectSerializer(serializers.Serializer):
    """Used by host to reject a visit"""
    rejection_reason = serializers.CharField()

    def save(self, visit, rejected_by):
        if not visit.can_transition_to(Visit.Status.REJECTED):
            raise serializers.ValidationError({
                "detail": "This visit cannot be rejected in its current state."
            })
        visit.status = Visit.Status.REJECTED
        visit.rejection_reason = self.validated_data['rejection_reason']
        visit.host_responded_at = timezone.now()
        visit.save(update_fields=['status', 'rejection_reason', 'host_responded_at', 'updated_at'])
        return visit


class VisitCancelSerializer(serializers.Serializer):
    """Used by security or host to cancel a visit"""
    cancellation_reason = serializers.CharField()

    def save(self, visit, cancelled_by):
        if not visit.can_transition_to(Visit.Status.CANCELLED):
            raise serializers.ValidationError({
                "detail": "This visit cannot be cancelled in its current state."
            })
        visit.status = Visit.Status.CANCELLED
        visit.cancellation_reason = self.validated_data['cancellation_reason']
        visit.cancelled_by = cancelled_by
        visit.save(update_fields=['status', 'cancellation_reason', 'cancelled_by', 'updated_at'])
        return visit


class VisitCheckOutSerializer(serializers.Serializer):
    """Used by security to check out a visitor"""
    def save(self, visit, checked_out_by):
        if not visit.can_transition_to(Visit.Status.CHECKED_OUT):
            raise serializers.ValidationError({
                "detail": "This visit cannot be checked out in its current state."
            })
        visit.status = Visit.Status.CHECKED_OUT
        visit.checked_out_at = timezone.now()
        visit.checked_out_by = checked_out_by
        visit.save(update_fields=['status', 'checked_out_at', 'checked_out_by', 'updated_at'])
        return visit


class VisitOverstaySerializer(serializers.Serializer):
    """Flags a visit as overstay"""
    def save(self, visit):
        if visit.is_overstaying():
            if not visit.can_transition_to(Visit.Status.OVERSTAY):
                raise serializers.ValidationError({
                    "detail": "This visit cannot be flagged as overstay in its current state."
                })
            visit.status = Visit.Status.OVERSTAY
            visit.overstay_flagged = True
            visit.overstay_flagged_at = timezone.now()
            visit.save(update_fields=[
                'status',
                'overstay_flagged',
                'overstay_flagged_at',
                'updated_at'
            ])
        return visit

class VisitExpireSerializer(serializers.Serializer):
    """Auto expires a visit if host hasn't responded"""
    def save(self, visit):
        if not visit.can_transition_to(Visit.Status.EXPIRED):
            raise serializers.ValidationError({
                "detail": "This visit cannot be expired in its current state."
            })
        visit.status = Visit.Status.EXPIRED
        visit.save(update_fields=['status', 'updated_at'])
        return visit


class QRScanSerializer(serializers.Serializer):
    """Used by security to scan a QR code and check in visitor"""
    qr_code_token = serializers.UUIDField()

    def validate_qr_code_token(self, value):
        try:
            visit = Visit.objects.select_related(
                'organisation__settings',
                'visitor',
                'host'
            ).get(qr_code_token=value)
        except Visit.DoesNotExist:
            raise serializers.ValidationError("Invalid QR code.")

        # Check emergency lockdown
        if visit.organisation.settings.emergency_lockdown:
            raise serializers.ValidationError("System is under emergency lockdown.")

        # Check QR validity
        if not visit.is_qr_valid():
            raise serializers.ValidationError("QR code is expired or invalid.")

        # Check valid transition
        if not visit.can_transition_to(Visit.Status.CHECKED_IN):
            raise serializers.ValidationError("This visit cannot be checked in.")

        self.visit = visit
        return value

    def save(self, checked_in_by):
        visit = self.visit
        visit.status = Visit.Status.CHECKED_IN
        visit.checked_in_at = timezone.now()
        visit.checked_in_by = checked_in_by
        visit.save(update_fields=['status', 'checked_in_at', 'checked_in_by', 'updated_at'])
        return visit


class EvacuationSerializer(serializers.ModelSerializer):
    """Used for emergency evacuation list"""
    visitor = VisitorMiniSerializer(read_only=True)
    host = UserMiniSerializer(read_only=True)

    class Meta:
        model = Visit
        fields = [
            'id',
            'visitor',
            'host',
            'checked_in_at',
            'expected_duration',
            'overstay_flagged',
        ]