import random
from django.utils import timezone
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'first_name',
            'last_name',
            'full_name',
            'role',
            'organisation',
            'department',
            'is_active',
            'date_joined',
        ]
        read_only_fields = ['id', 'date_joined']

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()


class UserMiniSerializer(serializers.ModelSerializer):
    """Lightweight - used when nested inside other serializers"""
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'full_name',
            'role',
            'department',
        ]

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
        style={"input_type": "password"}
    )
    confirm_password = serializers.CharField(
        write_only=True,
        style={"input_type": "password"}
    )

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'first_name',
            'last_name',
            'role',
            'organisation',
            'department',
            'password',
            'confirm_password',
        ]
        read_only_fields = ['id']

    def validate_email(self, value):
        return value.lower()

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'department',
        ]


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(
        write_only=True,
        style={"input_type": "password"}
    )
    new_password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
        style={"input_type": "password"}
    )
    confirm_new_password = serializers.CharField(
        write_only=True,
        style={"input_type": "password"}
    )

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_new_password']:
            raise serializers.ValidationError({"confirm_new_password": "Passwords do not match."})
        return attrs

    def save(self, user):
        if not user.check_password(self.validated_data['old_password']):
            raise serializers.ValidationError({"old_password": "Old password is incorrect."})
        user.set_password(self.validated_data['new_password'])
        user.save(update_fields=['password'])
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(
        write_only=True,
        style={"input_type": "password"}
    )

    def validate_email(self, value):
        return value.lower()

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
    
        user = authenticate(
            request=self.context.get('request'),
            email=email,
            password=password
        )

        if user is None:
            raise serializers.ValidationError({"detail": "Invalid credentials."})

        if not user.is_active:
            raise serializers.ValidationError({"detail": "Account is inactive."})

        attrs['user'] = user
        return attrs


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        return value.lower()

    def save(self):
        email = self.validated_data['email']
        try:
            user = User.objects.get(email=email)
            otp = str(random.randint(100000, 999999))
            user.otp = otp
            user.otp_created_at = timezone.now()
            user.save(update_fields=['otp', 'otp_created_at'])
            return user, otp
        except User.DoesNotExist:
            # Don't reveal if email exists or not
            return None, None


class PasswordResetCompleteSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)
    new_password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
        style={"input_type": "password"}
    )
    confirm_password = serializers.CharField(
        write_only=True,
        style={"input_type": "password"}
    )

    def validate_email(self, value):
        return value.lower()

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})

        try:
            user = User.objects.get(email=attrs['email'])
        except User.DoesNotExist:
            raise serializers.ValidationError({"detail": "Invalid credentials."})

        # Check OTP matches
        if user.otp != attrs['otp']:
            raise serializers.ValidationError({"otp": "Invalid OTP."})

        # Check OTP expiry - 10 minutes
        if not user.otp_created_at:
            raise serializers.ValidationError({"otp": "Invalid OTP."})

        otp_age = (timezone.now() - user.otp_created_at).total_seconds() / 60
        if otp_age > 10:
            raise serializers.ValidationError({"otp": "OTP has expired. Request a new one."})

        attrs['user'] = user
        return attrs

    def save(self):
        user = self.validated_data['user']
        user.set_password(self.validated_data['new_password'])
        user.otp = ''
        user.otp_created_at = None
        user.save(update_fields=['password', 'otp', 'otp_created_at'])
        return user