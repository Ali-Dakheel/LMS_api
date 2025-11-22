"""
Users API URLs - Split into auth and user management
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    # Auth
    LoginView,
    LogoutView,
    TokenRefreshView,
    RegisterView,
    # Password
    PasswordResetRequestView,
    PasswordResetConfirmView,
    ChangePasswordView,
    # Email
    EmailVerificationView,
    ResendEmailVerificationView,
    # Profile
    CurrentUserProfileView,
    UploadAvatarView,
    # User Management
    UserViewSet,
)

# Router for user management viewset
router = DefaultRouter()
router.register(r'', UserViewSet, basename='user')

# ============================================================================
# AUTHENTICATION URL PATTERNS (mounted at /api/v1/auth/)
# ============================================================================
auth_urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('register/', RegisterView.as_view(), name='register'),
    
    # Password management
    path('password/reset-request/', 
         PasswordResetRequestView.as_view(), 
         name='password-reset-request'),
    path('password/reset-confirm/', 
         PasswordResetConfirmView.as_view(), 
         name='password-reset-confirm'),
    path('password/change/', 
         ChangePasswordView.as_view(), 
         name='password-change'),
    
    # Email verification
    path('email/verify/', 
         EmailVerificationView.as_view(), 
         name='email-verify'),
    path('email/resend/', 
         ResendEmailVerificationView.as_view(), 
         name='email-resend'),
]

# ============================================================================
# USER MANAGEMENT URL PATTERNS (mounted at /api/v1/users/)
# ============================================================================
users_urlpatterns = [
    # Current user profile
    path('me/', 
         CurrentUserProfileView.as_view(), 
         name='current-user-profile'),
    path('me/avatar/', 
         UploadAvatarView.as_view(), 
         name='upload-avatar'),
    
    # User CRUD (admin) - handled by router
    # - GET    /api/v1/users/              → List users
    # - POST   /api/v1/users/              → Create user
    # - GET    /api/v1/users/{id}/         → Get user details
    # - PUT    /api/v1/users/{id}/         → Update user (full)
    # - PATCH  /api/v1/users/{id}/         → Update user (partial)
    # - DELETE /api/v1/users/{id}/         → Deactivate user
    # - POST   /api/v1/users/{id}/reactivate/  → Reactivate user
    # - GET    /api/v1/users/teachers/     → List teachers
    # - GET    /api/v1/users/students/     → List students
    # - GET    /api/v1/users/deans/        → List deans
    path('', include(router.urls)),
]