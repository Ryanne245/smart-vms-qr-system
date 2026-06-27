from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from drf_spectacular.utils import extend_schema

from django.contrib.auth import get_user_model

from .serializers import (
    LoginSerializer,
    UserSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    ChangePasswordSerializer,
    PasswordResetRequestSerializer,
    PasswordResetCompleteSerializer,
    UserMiniSerializer,
)
from core.permissions import (
    IsOrgAdminOrSuperAdmin,
    CanAccessHosts,
    BelongsToOrganisation,
)
from core.utils import create_audit_log, send_email_notification

User = get_user_model()

@extend_schema(request=LoginSerializer, responses={200:UserSerializer})
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            create_audit_log(
                request=request,
                action="USER_LOGIN",
                target_model="User",
                target_id=user.id,
                details={"email": user.email}
            )
            return Response({
                "user": UserSerializer(user).data,
                "tokens": {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                }
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(request=None, responses={200: None})
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response(
                    {"detail": "Refresh token is required."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            token = RefreshToken(refresh_token)
            token.blacklist()
            create_audit_log(
                request=request,
                action="USER_LOGOUT",
                target_model="User",
                target_id=request.user.id,
                details={"email": request.user.email}
            )
            return Response(
                {"detail": "Logged out successfully."},
                status=status.HTTP_200_OK
            )
        except TokenError:
            return Response(
                {"detail": "Invalid or expired token."},
                status=status.HTTP_400_BAD_REQUEST
            )


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            user, otp = serializer.save()
            if user and otp:
                send_email_notification(
                    recipient_email=user.email,
                    subject="Password Reset OTP",
                    message=f"Your password reset OTP is: {otp}. It expires in 10 minutes.",
                    notification_type="VISIT_CREATED",
                )
            return Response(
                {"detail": "If an account with this email exists, an OTP has been sent."},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetCompleteView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetCompleteSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"detail": "Password reset successful. You can now log in."},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class MeUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        serializer = UserUpdateSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            create_audit_log(
                request=request,
                action="USER_UPDATED",
                target_model="User",
                target_id=request.user.id,
                details={"updated_fields": list(request.data.keys())}
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            create_audit_log(
                request=request,
                action="USER_UPDATED",
                target_model="User",
                target_id=request.user.id,
                details={"action": "password_changed"}
            )
            return Response(
                {"detail": "Password changed successfully."},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserListView(APIView):
    permission_classes = [IsAuthenticated, IsOrgAdminOrSuperAdmin]

    def get(self, request):
        if request.user.role == "SUPER_ADMIN":
            users = User.objects.all()
        else:
            users = User.objects.filter(organisation=request.user.organisation)

        role = request.query_params.get('role')
        department = request.query_params.get('department')

        if role:
            users = users.filter(role=role)
        if department:
            users = users.filter(department=department)

        serializer = UserSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserCreateView(APIView):
    permission_classes = [IsAuthenticated, IsOrgAdminOrSuperAdmin, BelongsToOrganisation]

    def post(self, request):
        serializer = UserCreateSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            if request.user.role == "ORG_ADMIN":
                user.organisation = request.user.organisation
                user.save(update_fields=['organisation'])
            create_audit_log(
                request=request,
                action="USER_CREATED",
                target_model="User",
                target_id=user.id,
                details={"email": user.email, "role": user.role}
            )
            return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserDetailView(APIView):
    permission_classes = [IsAuthenticated, IsOrgAdminOrSuperAdmin]

    def get(self, request, user_id):
        try:
            if request.user.role == "SUPER_ADMIN":
                user = User.objects.get(id=user_id)
            else:
                user = User.objects.get(
                    id=user_id,
                    organisation=request.user.organisation
                )
        except User.DoesNotExist:
            return Response(
                {"detail": "User not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserDeactivateView(APIView):
    permission_classes = [IsAuthenticated, IsOrgAdminOrSuperAdmin]
    def put(self, request, user_id):
        try:
            if request.user.role == "SUPER_ADMIN":
                user = User.objects.get(id=user_id)
            else:
                user = User.objects.get(
                    id=user_id,
                    organisation=request.user.organisation
                )
        except User.DoesNotExist:
            return Response(
                {"detail": "User not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        if user == request.user:
            return Response(
                {"detail": "You cannot deactivate your own account."},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.is_active = False
        user.save(update_fields=['is_active'])
        create_audit_log(
            request=request,
            action="USER_DEACTIVATED",
            target_model="User",
            target_id=user.id,
            details={"email": user.email}
        )
        return Response(
            {"detail": "User deactivated successfully."},
            status=status.HTTP_200_OK
        )


class HostListView(APIView):
    permission_classes = [IsAuthenticated, CanAccessHosts, BelongsToOrganisation]

    def get(self, request):
        hosts = User.objects.filter(
            organisation=request.user.organisation,
            role="HOST",
            is_active=True,
        )
        search = request.query_params.get('search')
        department = request.query_params.get('department')

        if search:
            hosts = hosts.filter(
                first_name__icontains=search
            ) | hosts.filter(
                last_name__icontains=search
            )
        if department:
            hosts = hosts.filter(department__icontains=department)

        serializer = UserMiniSerializer(hosts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)