"""
Users API Views

Exports all view classes for URL routing.
"""

from .auth import (
    LoginView,
    LogoutView,
    TokenRefreshView,
    RegisterView,
)

from .password import (
    PasswordResetRequestView,
    PasswordResetConfirmView,
    ChangePasswordView,
)

from .email import (
    EmailVerificationView,
    ResendEmailVerificationView,
)

from .profile import (
    CurrentUserProfileView,
    UploadAvatarView,
)

from .user_management import UserViewSet

__all__ = [
    # Auth
    'LoginView',
    'LogoutView',
    'TokenRefreshView',
    'RegisterView',
    
    # Password
    'PasswordResetRequestView',
    'PasswordResetConfirmView',
    'ChangePasswordView',
    
    # Email
    'EmailVerificationView',
    'ResendEmailVerificationView',
    
    # Profile
    'CurrentUserProfileView',
    'UploadAvatarView',
    
    # User Management
    'UserViewSet',
]