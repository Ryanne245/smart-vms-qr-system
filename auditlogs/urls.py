from django.urls import path
from .views import (
    AuditLogListView,
    AuditLogDetailView,
)

urlpatterns = [
    path('', AuditLogListView.as_view(), name='auditlog-list'),
    path('<uuid:log_id>/', AuditLogDetailView.as_view(), name='auditlog-detail'),
]