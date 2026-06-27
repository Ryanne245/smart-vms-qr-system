from django.urls import path
from .views import (
    VisitListCreateView,
    VisitActiveView,
    VisitPendingView,
    VisitHistoryView,
    VisitMyVisitsView,
    VisitRegisteredByMeView,
    VisitEvacuationView,
    QRScanView,
    VisitDetailView,
    VisitQRView,
    VisitQRRegenerateView,
    VisitApproveView,
    VisitRejectView,
    VisitCancelView,
    VisitCheckOutView,
    VisitNotesView,
)

urlpatterns = [
    # List and create
    path('', VisitListCreateView.as_view(), name='visit-list-create'),

    # Static endpoints - must come before <uuid:visit_id>/
    path('active/', VisitActiveView.as_view(), name='visit-active'),
    path('pending/', VisitPendingView.as_view(), name='visit-pending'),
    path('history/', VisitHistoryView.as_view(), name='visit-history'),
    path('my-visits/', VisitMyVisitsView.as_view(), name='visit-my-visits'),
    path('registered-by-me/', VisitRegisteredByMeView.as_view(), name='visit-registered-by-me'),
    path('evacuation/', VisitEvacuationView.as_view(), name='visit-evacuation'),
    path('scan-qr/', QRScanView.as_view(), name='visit-scan-qr'),

    # Dynamic endpoints - uuid based
    path('<uuid:visit_id>/', VisitDetailView.as_view(), name='visit-detail'),
    path('<uuid:visit_id>/qr/', VisitQRView.as_view(), name='visit-qr'),
    path('<uuid:visit_id>/qr/regenerate/', VisitQRRegenerateView.as_view(), name='visit-qr-regenerate'),
    path('<uuid:visit_id>/approve/', VisitApproveView.as_view(), name='visit-approve'),
    path('<uuid:visit_id>/reject/', VisitRejectView.as_view(), name='visit-reject'),
    path('<uuid:visit_id>/cancel/', VisitCancelView.as_view(), name='visit-cancel'),
    path('<uuid:visit_id>/checkout/', VisitCheckOutView.as_view(), name='visit-checkout'),
    path('<uuid:visit_id>/notes/', VisitNotesView.as_view(), name='visit-notes'),
]