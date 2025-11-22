"""
Authentication Views

Handles:
- User login (JWT token generation)
- User logout (token blacklisting)
- Token refresh
- User registration (admin only)
"""

import logging
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from core.responses import success_response, error_response
from core.permissions import IsAdmin
from ..serializers import (
    LoginSerializer,
    TokenRefreshSerializer,
    RegisterSerializer,
    UserProfileSerializer,
    UserDetailSerializer,
)

logger = logging.getLogger(__name__)


class LoginView(APIView):
    """
    User login with JWT token generation.
    
    Endpoint: POST /api/v1/auth/login/
    Permission: Public (AllowAny)
    Throttle: 'login' scope
    
    Request Body:
        email: User email (string, required)
        password: User password (string, required)
    
    Response:
        access: JWT access token (24h validity)
        refresh: JWT refresh token (7d validity)
        user: User profile data
    """
    
    permission_classes = [AllowAny]
    throttle_scope = 'login'
    
    def post(self, request):
        """Handle login request."""
        serializer = LoginSerializer(data=request.data)
        
        if not serializer.is_valid():
            logger.warning(f"Login failed for email: {request.data.get('email')}")
            return error_response(
                message="Login failed",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate tokens
        result = serializer.save()
        user = result['user']
        
        # Update activity tracking
        user.update_last_seen(
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT')
        )
        
        logger.info(f"User {user.id} ({user.email}) logged in successfully")
        
        return success_response(
            data={
                'access': result['access'],
                'refresh': result['refresh'],
                'user': UserProfileSerializer(user).data
            },
            message="Login successful",
            status_code=status.HTTP_200_OK
        )


class LogoutView(APIView):
    """
    User logout (blacklist refresh token).
    
    Endpoint: POST /api/v1/auth/logout/
    Permission: Authenticated users
    
    Request Body:
        refresh: JWT refresh token (string, required)
    
    Note: Access token remains valid until expiration.
    Client should discard both tokens immediately.
    """
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Handle logout request."""
        refresh_token = request.data.get('refresh')
        
        if not refresh_token:
            return error_response(
                message="Refresh token is required",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Blacklist the refresh token
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            logger.info(f"User {request.user.id} logged out successfully")
            
            return success_response(
                message="Logout successful",
                status_code=status.HTTP_200_OK
            )
        
        except TokenError as e:
            logger.warning(f"Logout failed with invalid token: {str(e)}")
            return error_response(
                message="Invalid or expired token",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        except Exception as e:
            logger.error(f"Logout error: {str(e)}", exc_info=True)
            return error_response(
                message=f"Logout failed: {str(e)}",
                status_code=status.HTTP_400_BAD_REQUEST
            )


class TokenRefreshView(APIView):
    """
    Refresh access token using refresh token.
    
    Endpoint: POST /api/v1/auth/refresh/
    Permission: Public (AllowAny)
    
    Request Body:
        refresh: JWT refresh token (string, required)
    
    Response:
        access: New JWT access token
    """
    
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Handle token refresh request."""
        serializer = TokenRefreshSerializer(data=request.data)
        
        if not serializer.is_valid():
            logger.warning("Token refresh failed with invalid token")
            return error_response(
                message="Token refresh failed",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        return success_response(
            data={'access': serializer.validated_data['access']},
            message="Token refreshed successfully",
            status_code=status.HTTP_200_OK
        )


class RegisterView(APIView):
    """
    Register new user (admin only).
    
    Endpoint: POST /api/v1/auth/register/
    Permission: Admin only
    
    Request Body:
        email: User email (string, required)
        name: User full name (string, required)
        role: User role (string, required: admin/dean/teacher/student)
        password: User password (string, required, min 8 chars)
        password_confirm: Password confirmation (string, required)
        institution: Institution name (string, optional)
        department: Department name (string, optional)
        major: Major/program (string, optional)
    
    Note: Academic fields required based on role.
    """
    
    permission_classes = [IsAdmin]
    
    def post(self, request):
        """Handle user registration."""
        serializer = RegisterSerializer(data=request.data)
        
        if not serializer.is_valid():
            logger.warning(f"Registration failed: {serializer.errors}")
            return error_response(
                message="Registration failed",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        user = serializer.save()
        
        logger.info(
            f"User registered by admin {request.user.id}: "
            f"{user.id} ({user.email}, role: {user.role})"
        )
        
        return success_response(
            data=UserDetailSerializer(user).data,
            message="User registered successfully",
            status_code=status.HTTP_201_CREATED
        )