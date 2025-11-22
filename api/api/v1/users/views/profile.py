"""
User Profile Views

Handles:
- Get current user profile
- Update current user profile
- Upload profile image/avatar
"""

import logging
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from core.responses import success_response, error_response
from ..serializers import (
    UserProfileSerializer,
    UpdateProfileSerializer,
)

logger = logging.getLogger(__name__)


class CurrentUserProfileView(APIView):
    """
    Get or update current authenticated user's profile.
    
    Endpoints:
        GET /api/v1/users/me/ - Get profile
        PATCH /api/v1/users/me/ - Update profile
    
    Permission: Authenticated users
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        Get current user profile.
        
        Returns:
            User profile data with role-specific info
        
        Side effects:
            Updates last_seen, last_ip_address, last_user_agent
        """
        serializer = UserProfileSerializer(request.user)
        
        # Update activity tracking
        request.user.update_last_seen(
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT')
        )
        
        return success_response(
            data=serializer.data,
            message="Profile retrieved successfully",
            status_code=status.HTTP_200_OK
        )
    
    def patch(self, request):
        """
        Update current user profile (partial update).
        
        Updatable fields:
            - name
            - profile_image
            - institution (role-dependent)
            - department (role-dependent)
            - major (role-dependent)
        
        Restrictions:
            - Admin cannot modify academic fields
            - Role, email, and account status are read-only
        """
        serializer = UpdateProfileSerializer(
            request.user,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        
        if not serializer.is_valid():
            logger.warning(
                f"Profile update failed for user {request.user.id}: "
                f"{serializer.errors}"
            )
            return error_response(
                message="Profile update failed",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        serializer.save()
        
        logger.info(
            f"Profile updated for user {request.user.id}: "
            f"{list(request.data.keys())}"
        )
        
        return success_response(
            data=UserProfileSerializer(request.user).data,
            message="Profile updated successfully",
            status_code=status.HTTP_200_OK
        )


class UploadAvatarView(APIView):
    """
    Upload profile image/avatar.
    
    Endpoint: POST /api/v1/users/me/avatar/
    Permission: Authenticated users
    
    Request:
        Content-Type: multipart/form-data
        Body: profile_image file
    
    Validation:
        - Max size: 5MB
        - Allowed formats: jpg, jpeg, png, gif
    """
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Handle profile image upload."""
        profile_image = request.FILES.get('profile_image')
        
        if not profile_image:
            return error_response(
                message="No image file provided",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = UpdateProfileSerializer(
            request.user,
            data={'profile_image': profile_image},
            partial=True,
            context={'request': request}
        )
        
        if not serializer.is_valid():
            logger.warning(
                f"Image upload failed for user {request.user.id}: "
                f"{serializer.errors}"
            )
            return error_response(
                message="Image upload failed",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        serializer.save()
        
        logger.info(f"Profile image uploaded for user {request.user.id}")
        
        return success_response(
            data={
                'profile_image': (
                    request.user.profile_image.url
                    if request.user.profile_image
                    else None
                )
            },
            message="Profile image uploaded successfully",
            status_code=status.HTTP_200_OK
        )