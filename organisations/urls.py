from django.urls import path
from .views import (
    OrganisationListCreateView,
    OrganisationMineView,
    OrganisationDetailView,
    OrganisationDeactivateView,
    OrganisationSettingsView,
    OrganisationLockdownView,
)

urlpatterns = [
    # Organisation endpoints
    path('', OrganisationListCreateView.as_view(), name='organisation-list-create'),
    path('mine/', OrganisationMineView.as_view(), name='organisation-mine'),
    path('<uuid:org_id>/', OrganisationDetailView.as_view(), name='organisation-detail'),
    path('<uuid:org_id>/deactivate/', OrganisationDeactivateView.as_view(), name='organisation-deactivate'),
    path('<uuid:org_id>/settings/', OrganisationSettingsView.as_view(), name='organisation-settings'),
    path('<uuid:org_id>/lockdown/', OrganisationLockdownView.as_view(), name='organisation-lockdown'),
]