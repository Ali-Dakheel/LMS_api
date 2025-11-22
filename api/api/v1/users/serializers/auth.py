"""
Authentication Serializers

Handles:
- Login (JWT token generation)
- Token refresh
- User registration (admin only)
"""

from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from apps.users.models import User


class LoginSerializer(serializers.Serializer):
    """
    User login serializer.
    
    Validates credentials and generates JWT tokens.
    """
    
    email = serializers.EmailField()
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )
    
    def validate(self, attrs):
        """
        Authenticate user and validate account status.
        
        Raises:
            ValidationError: If credentials invalid or account inactive
        """
        email = attrs.get('email', '').lower()
        password = attrs.get('password')
        
        if not email or not password:
            raise serializers.ValidationError(
                "Email and password are required",
                code='required_fields'
            )
        
        # Authenticate user
        user = authenticate(username=email, password=password)
        
        if not user:
            raise serializers.ValidationError(
                "Invalid email or password",
                code='invalid_credentials'
            )
        
        if not user.is_active:
            raise serializers.ValidationError(
                "Your account has been deactivated. Please contact support",
                code='account_inactive'
            )
        
        attrs['user'] = user
        return attrs
    
    def create(self, validated_data):
        """
        Generate JWT tokens and update last login.
        
        Returns:
            dict: Contains user, access token, and refresh token
        """
        user = validated_data['user']
        
        # Update last login timestamp
        user.last_login_at = timezone.now()
        user.save(update_fields=['last_login_at'])
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return {
            'user': user,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }


class TokenRefreshSerializer(serializers.Serializer):
    """
    Token refresh serializer.
    
    Validates refresh token and generates new access token.
    """
    
    refresh = serializers.CharField()
    
    def validate(self, attrs):
        """
        Validate refresh token and generate new access token.
        
        Raises:
            ValidationError: If refresh token invalid or expired
        """        
        try:
            refresh = RefreshToken(attrs['refresh'])
            attrs['access'] = str(refresh.access_token)
        except TokenError:
            raise serializers.ValidationError(
                "Invalid or expired refresh token",
                code='invalid_token'
            )
        
        return attrs


class RegisterSerializer(serializers.ModelSerializer):
    """
    User registration serializer (admin only).
    
    Validates email uniqueness and password strength.
    """
    
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = User
        fields = [
            'email', 'name', 'role', 'password', 'password_confirm',
            'institution', 'department', 'major'
        ]
    
    def validate_email(self, value):
        """Validate email is unique and lowercase."""
        value = value.lower()
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "User with this email already exists",
                code='email_exists'
            )
        return value
    
    def validate(self, attrs):
        """Validate password match and strength."""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError(
                {"password_confirm": "Passwords do not match"},
                code='password_mismatch'
            )
        
        # Validate password strength
        try:
            validate_password(attrs['password'])
        except DjangoValidationError as e:
            raise serializers.ValidationError(
                {"password": list(e.messages)},
                code='weak_password'
            )
        
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        try:
            user = User.objects.create_user(
                password=password,
                **validated_data
            )
            return user
        except Exception as e:
            raise serializers.ValidationError(
                f"Failed to create user: {str(e)}",
                code='creation_failed'
            )
