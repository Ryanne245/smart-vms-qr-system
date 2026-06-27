from django.urls import path
from .views import (
    LoginView,
    LogoutView,
    PasswordResetRequestView,
    PasswordResetCompleteView,
    MeView,
    MeUpdateView,
    ChangePasswordView,
    UserListView,
    UserCreateView,
    UserDetailView,
    UserDeactivateView,
    HostListView,
)

urlpatterns = [
    # Auth endpoints
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('password-reset/request/', PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('password-reset/complete/', PasswordResetCompleteView.as_view(), name='password-reset-complete'),

    # Me endpoints
    path('me/', MeView.as_view(), name='me'),
    path('me/update/', MeUpdateView.as_view(), name='me-update'),
    path('me/change-password/', ChangePasswordView.as_view(), name='change-password'),

    # User management endpoints
    path('', UserListView.as_view(), name='user-list'),
    path('create/', UserCreateView.as_view(), name='user-create'),
    path('hosts/', HostListView.as_view(), name='host-list'),
    path('<uuid:user_id>/', UserDetailView.as_view(), name='user-detail'),
    path('<uuid:user_id>/deactivate/', UserDeactivateView.as_view(), name='user-deactivate'),
]