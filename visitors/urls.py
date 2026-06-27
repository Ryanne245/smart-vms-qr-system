from django.urls import path
from .views import (
    VisitorListCreateView,
    VisitorSearchView,
    VisitorDetailView,
    VisitorBlacklistView,
    VisitorUnblacklistView,
    VisitorVisitHistoryView,
)

urlpatterns = [
    path('', VisitorListCreateView.as_view(), name='visitor-list-create'),
    path('search/', VisitorSearchView.as_view(), name='visitor-search'),
    path('<uuid:visitor_id>/', VisitorDetailView.as_view(), name='visitor-detail'),
    path('<uuid:visitor_id>/blacklist/', VisitorBlacklistView.as_view(), name='visitor-blacklist'),
    path('<uuid:visitor_id>/unblacklist/', VisitorUnblacklistView.as_view(), name='visitor-unblacklist'),
    path('<uuid:visitor_id>/visit-history/', VisitorVisitHistoryView.as_view(), name='visitor-visit-history'),
]