"""
Users API Serializers

Exports all serializers for easy importing in views.
"""

# Authentication
from .auth import (
    LoginSerializer,
    TokenRefreshSerializer,
    RegisterSerializer,
)

# Password Management
from .password import (
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    ChangePasswordSerializer,
)

# Email Verification
from .email import (
    EmailVerificationSerializer,
    ResendEmailVerificationSerializer,
)

# Profile
from .profile import (
    TeacherInfoSerializer,
    StudentInfoSerializer,
    UserProfileSerializer,
    UpdateProfileSerializer,
)

# User Management
from .user_management import (
    UserListSerializer,
    UserDetailSerializer,
    UserCreateUpdateSerializer,
)

__all__ = [
    # Auth
    'LoginSerializer',
    'TokenRefreshSerializer',
    'RegisterSerializer',
    
    # Password
    'PasswordResetRequestSerializer',
    'PasswordResetConfirmSerializer',
    'ChangePasswordSerializer',
    
    # Email
    'EmailVerificationSerializer',
    'ResendEmailVerificationSerializer',
    
    # Profile
    'TeacherInfoSerializer',
    'StudentInfoSerializer',
    'UserProfileSerializer',
    'UpdateProfileSerializer',
    
    # User Management
    'UserListSerializer',
    'UserDetailSerializer',
    'UserCreateUpdateSerializer',
]