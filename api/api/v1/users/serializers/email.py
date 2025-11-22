"""
Email Verification Serializers

Handles:
- Email verification with token
- Resend verification email
"""

from rest_framework import serializers
from apps.users.models import User, EmailVerificationToken, verify_email_via_token


class EmailVerificationSerializer(serializers.Serializer):
    """Email verification serializer."""
    
    token = serializers.CharField()
    
    def validate_token(self, value):
        """Verify token is valid."""
        token_obj = EmailVerificationToken.verify_token(value)
        if not token_obj:
            raise serializers.ValidationError(
                "Invalid or expired token",
                code='invalid_token'
            )
        return value
    
    def save(self):
        """Verify user email using token."""
        token = self.validated_data['token']
        user = verify_email_via_token(token)
        return user


class ResendEmailVerificationSerializer(serializers.Serializer):
    """Resend email verification serializer."""
    
    email = serializers.EmailField()
    
    def validate_email(self, value):
        """Check if user exists and not already verified."""
        value = value.lower()
        
        try:
            user = User.objects.get(email=value)
            if user.email_verified:
                raise serializers.ValidationError(
                    "Email is already verified",
                    code='already_verified'
                )
        except User.DoesNotExist:
            raise serializers.ValidationError(
                "User not found",
                code='user_not_found'
            )
        
        return value
    
    def save(self):
        """Create new verification token."""
        email = self.validated_data['email']
        user = User.objects.get(email=email)
        raw_token, token_obj = EmailVerificationToken.create_token(user)
        return {'user': user, 'token': raw_token}