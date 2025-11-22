"""
Password Management Serializers

Handles:
- Password reset request
- Password reset confirmation
- Password change (authenticated users)
"""

from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError

from apps.users.models import User, PasswordResetToken


class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Password reset request serializer.
    
    Security: Doesn't reveal if email exists (prevents enumeration).
    """
    
    email = serializers.EmailField()
    
    def validate_email(self, value):
        """
        Validate email format (don't check existence for security).
        
        Note: We check existence in save() but don't reveal it in validation.
        """
        value = value.lower()
        
        # Silent validation - check if active but don't reveal
        try:
            user = User.objects.get(email=value)
            if not user.is_active:
                # Don't reveal account is deactivated
                pass
        except User.DoesNotExist:
            # Don't reveal user doesn't exist
            pass
        
        return value
    
    def save(self):
        """
        Create password reset token if user exists and is active.
        
        Returns:
            dict or None: User and token if successful, None otherwise
        """
        email = self.validated_data['email']
        
        try:
            user = User.objects.get(email=email, is_active=True)
            raw_token, token_obj = PasswordResetToken.create_token(user)
            return {'user': user, 'token': raw_token}
        except (User.DoesNotExist, DjangoValidationError):
            # Return None silently (don't reveal user doesn't exist)
            return None


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Password reset confirmation serializer.
    
    Validates token and sets new password.
    """
    
    token = serializers.CharField()
    new_password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )
    
    def validate(self, attrs):
        """Validate token and password."""
        token = attrs.get('token')
        new_password = attrs.get('new_password')
        new_password_confirm = attrs.get('new_password_confirm')
        
        # Check passwords match
        if new_password != new_password_confirm:
            raise serializers.ValidationError(
                {"new_password_confirm": "Passwords do not match"},
                code='password_mismatch'
            )
        
        # Verify token
        token_obj = PasswordResetToken.verify_token(token)
        if not token_obj:
            raise serializers.ValidationError(
                {"token": "Invalid or expired token"},
                code='invalid_token'
            )
        
        # Validate password strength
        try:
            validate_password(new_password, user=token_obj.user)
        except DjangoValidationError as e:
            raise serializers.ValidationError(
                {"new_password": list(e.messages)},
                code='weak_password'
            )
        
        attrs['token_obj'] = token_obj
        return attrs
    
    def save(self):
        """Reset password and mark token as used."""
        token_obj = self.validated_data['token_obj']
        new_password = self.validated_data['new_password']
        
        user = token_obj.user
        user.set_password(new_password)
        user.save()
        
        token_obj.mark_used()
        
        return user


class ChangePasswordSerializer(serializers.Serializer):
    """
    Password change serializer for authenticated users.
    
    Enforces:
    - Old password verification
    - Password strength validation
    - Password history check (via model method)
    """
    
    old_password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )
    
    def validate(self, attrs):
        """Validate old password and new password match."""
        user = self.context['request'].user
        old_password = attrs.get('old_password')
        new_password = attrs.get('new_password')
        new_password_confirm = attrs.get('new_password_confirm')
        
        # Check old password
        if not user.check_password(old_password):
            raise serializers.ValidationError(
                {"old_password": "Current password is incorrect"},
                code='incorrect_password'
            )
        
        # Check passwords match
        if new_password != new_password_confirm:
            raise serializers.ValidationError(
                {"new_password_confirm": "Passwords do not match"},
                code='password_mismatch'
            )
        
        # Validate password strength
        try:
            validate_password(new_password, user=user)
        except DjangoValidationError as e:
            raise serializers.ValidationError(
                {"new_password": list(e.messages)},
                code='weak_password'
            )
        
        return attrs
    
    def save(self):
        """
        Change password using model method.
        
        Model method enforces password history check.
        """
        user = self.context['request'].user
        old_password = self.validated_data['old_password']
        new_password = self.validated_data['new_password']
        
        # Use model method which checks password history
        try:
            user.change_password(old_password, new_password)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.message_dict)
        
        return user