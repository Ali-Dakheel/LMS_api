"""
Password Management Views

Handles:
- Password reset request (email-based)
- Password reset confirmation
- Password change (authenticated users)
"""

import logging
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status

from core.responses import success_response, error_response
from ..serializers import (
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    ChangePasswordSerializer,
)

logger = logging.getLogger(__name__)


class PasswordResetRequestView(APIView):
    """
    Request password reset (sends email with token).
    
    Endpoint: POST /api/v1/auth/password/reset-request/
    Permission: Public (AllowAny)
    Throttle: 'password_reset' scope (3 requests/hour)
    
    Request Body:
        email: User email (string, required)
    
    Security:
        - Always returns success (doesn't reveal if email exists)
        - Rate limited (3 requests per 5 minutes per user)
        - Token expires in 24 hours
        - One-time use tokens
    
    Note: Email sending is currently stubbed (TODO).
    """
    
    permission_classes = [AllowAny]
    throttle_scope = 'password_reset'
    
    def post(self, request):
        """Handle password reset request."""
        serializer = PasswordResetRequestSerializer(data=request.data)
        
        if not serializer.is_valid():
            return error_response(
                message="Invalid request",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        result = serializer.save()
        
        if result:
            # TODO: Send email with token
            # from core.email import send_password_reset_email
            # send_password_reset_email(result['user'], result['token'])
            
            logger.info(
                f"Password reset token generated for user {result['user'].id}"
            )
        else:
            # User doesn't exist, but don't reveal it
            logger.debug(
                f"Password reset requested for non-existent email: "
                f"{request.data.get('email')}"
            )
        
        # Always return success (security: don't reveal if user exists)
        return success_response(
            message="If the email exists, a password reset link has been sent.",
            status_code=status.HTTP_200_OK
        )


class PasswordResetConfirmView(APIView):
    """
    Confirm password reset with token.
    
    Endpoint: POST /api/v1/auth/password/reset-confirm/
    Permission: Public (AllowAny)
    
    Request Body:
        token: Reset token from email (string, required)
        new_password: New password (string, required, min 8 chars)
        new_password_confirm: Password confirmation (string, required)
    
    Security:
        - Token must be valid and not expired
        - Token can only be used once
        - Password strength validated
    """
    
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Handle password reset confirmation."""
        serializer = PasswordResetConfirmSerializer(data=request.data)
        
        if not serializer.is_valid():
            logger.warning("Password reset confirmation failed with invalid data")
            return error_response(
                message="Password reset failed",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        user = serializer.save()
        
        logger.info(f"Password reset successful for user {user.id} ({user.email})")
        
        return success_response(
            message="Password reset successful. You can now login with your new password.",
            status_code=status.HTTP_200_OK
        )


class ChangePasswordView(APIView):
    """
    Change password for authenticated user.
    
    Endpoint: POST /api/v1/auth/password/change/
    Permission: Authenticated users
    
    Request Body:
        old_password: Current password (string, required)
        new_password: New password (string, required, min 8 chars)
        new_password_confirm: Password confirmation (string, required)
    
    Security:
        - Old password must be correct
        - New password strength validated
        - Cannot reuse last 5 passwords
        - Password history tracked
    """
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Handle password change request."""
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if not serializer.is_valid():
            logger.warning(
                f"Password change failed for user {request.user.id}: "
                f"{serializer.errors}"
            )
            return error_response(
                message="Password change failed",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        serializer.save()
        
        logger.info(f"Password changed successfully for user {request.user.id}")
        
        return success_response(
            message="Password changed successfully",
            status_code=status.HTTP_200_OK
        )