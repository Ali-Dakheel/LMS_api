"""
Email Verification Views

Handles:
- Email verification with token
- Resend verification email
"""

import logging
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework import status

from core.responses import success_response, error_response
from ..serializers import (
    EmailVerificationSerializer,
    ResendEmailVerificationSerializer,
)

logger = logging.getLogger(__name__)


class EmailVerificationView(APIView):
    """
    Verify email with token.
    
    Endpoint: POST /api/v1/auth/email/verify/
    Permission: Public (AllowAny)
    
    Request Body:
        token: Verification token from email (string, required)
    
    Security:
        - Token must be valid and not expired
        - Token can only be used once
        - Token expires in 48 hours
    """
    
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Handle email verification."""
        serializer = EmailVerificationSerializer(data=request.data)
        
        if not serializer.is_valid():
            logger.warning("Email verification failed with invalid token")
            return error_response(
                message="Email verification failed",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        user = serializer.save()
        
        logger.info(f"Email verified for user {user.id} ({user.email})")
        
        return success_response(
            data={'email': user.email, 'verified': True},
            message="Email verified successfully",
            status_code=status.HTTP_200_OK
        )


class ResendEmailVerificationView(APIView):
    """
    Resend email verification.
    
    Endpoint: POST /api/v1/auth/email/resend/
    Permission: Public (AllowAny)
    Throttle: 'password_reset' scope (reused for email verification)
    
    Request Body:
        email: User email (string, required)
    
    Note: Email sending is currently stubbed (TODO).
    """
    
    permission_classes = [AllowAny]
    throttle_scope = 'password_reset'
    
    def post(self, request):
        """Handle resend verification email."""
        serializer = ResendEmailVerificationSerializer(data=request.data)
        
        if not serializer.is_valid():
            return error_response(
                message="Request failed",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        result = serializer.save()
        
        # TODO: Send email with token
        # from core.email import send_email_verification
        # send_email_verification(result['user'], result['token'])
        
        logger.info(
            f"Verification email resent for user {result['user'].id} "
            f"({result['user'].email})"
        )
        
        return success_response(
            message="Verification email sent",
            status_code=status.HTTP_200_OK
        )