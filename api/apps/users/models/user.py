"""
Core User Model - Smart Learning Hub

Handles:
- User authentication (email-based)
- Role-based access control (Admin, Dean, Teacher, Student)
- Activity tracking
- Account management
"""

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models, transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
import logging

from .profiles import PasswordHistory
from .managers import UserManager

logger = logging.getLogger(__name__)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model with role-based access control.
    
    Features:
    - Email-based authentication
    - Four roles: admin, dean, teacher, student
    - Activity tracking for analytics
    - Soft delete with deactivation
    """
    
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('dean', 'Dean'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
    ]
    
    # ============================================================================
    # AUTHENTICATION FIELDS
    # ============================================================================
    email = models.EmailField(
        unique=True,
        db_index=True,
        help_text="Primary login identifier"
    )
    
    # ============================================================================
    # PROFILE FIELDS
    # ============================================================================
    name = models.CharField(max_length=255)
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        db_index=True,
        help_text="User role determines access permissions"
    )
    profile_image = models.ImageField(
        upload_to='profile-images/',
        null=True,
        blank=True
    )
    
    # ============================================================================
    # ORGANIZATIONAL FIELDS
    # ============================================================================
    institution = models.CharField(max_length=255, blank=True)
    department = models.CharField(max_length=255, blank=True)
    major = models.CharField(max_length=255, blank=True)
    
    # ============================================================================
    # ACCOUNT STATUS
    # ============================================================================
    is_active = models.BooleanField(default=True, db_index=True)
    is_staff = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)
    email_verified_at = models.DateTimeField(null=True, blank=True)
    
    # Deactivation tracking
    deactivated_at = models.DateTimeField(null=True, blank=True)
    deactivation_reason = models.TextField(blank=True)
    
    # ============================================================================
    # ACTIVITY TRACKING
    # ============================================================================
    last_login_at = models.DateTimeField(null=True, blank=True)
    last_seen_at = models.DateTimeField(null=True, blank=True)
    last_page_path = models.CharField(max_length=500, blank=True)
    last_ip_address = models.GenericIPAddressField(null=True, blank=True)
    last_user_agent = models.CharField(max_length=500, blank=True)
    
    # ============================================================================
    # TIMESTAMPS
    # ============================================================================
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # ============================================================================
    # MANAGER & CONFIG
    # ============================================================================
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name', 'role']
    
    class Meta:
        db_table = 'users'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role']),
            models.Index(fields=['is_active']),
            models.Index(fields=['role', 'is_active']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.role})"
    
    # ============================================================================
    # ACCOUNT MANAGEMENT METHODS
    # ============================================================================
    
    @transaction.atomic
    def deactivate(self, reason=''):
        """
        Deactivate user account and invalidate tokens.
        
        Performs:
        - Marks account as inactive
        - Blacklists all JWT tokens
        - Drops active enrollments (students)
        - Removes primary teacher status (teachers/deans)
        
        Args:
            reason: Reason for deactivation (for audit trail)
        """
        from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
        
        self.is_active = False
        self.deactivated_at = timezone.now()
        self.deactivation_reason = reason
        self.save(update_fields=['is_active', 'deactivated_at', 'deactivation_reason'])
        
        # Blacklist all tokens
        OutstandingToken.objects.filter(user=self).delete()
        logger.info(f"Deactivated user {self.id} ({self.email}): {reason}")
        
        # Role-specific cleanup
        if self.role == 'student':
            self._cleanup_student_enrollments()
        elif self.role in ['teacher', 'dean']:
            self._cleanup_teacher_assignments()
    
    def reactivate(self):
        """Reactivate a deactivated user account."""
        self.is_active = True
        self.deactivated_at = None
        self.deactivation_reason = ''
        self.save(update_fields=['is_active', 'deactivated_at', 'deactivation_reason'])
        logger.info(f"Reactivated user {self.id} ({self.email})")
    
    # ============================================================================
    # ACTIVITY TRACKING METHODS
    # ============================================================================
    
    def update_last_seen(self, ip_address=None, user_agent=None):
        """
        Update last seen timestamp and optional metadata.
        
        Called on every API request by middleware.
        
        Args:
            ip_address: User's IP address
            user_agent: User's browser/client information
        """
        update_fields = ['last_seen_at']
        self.last_seen_at = timezone.now()
        
        if ip_address:
            self.last_ip_address = ip_address
            update_fields.append('last_ip_address')
        
        if user_agent:
            self.last_user_agent = user_agent[:500]
            update_fields.append('last_user_agent')
        
        self.save(update_fields=update_fields)
    
    # ============================================================================
    # EMAIL VERIFICATION
    # ============================================================================
    
    def verify_email(self):
        """Mark email as verified with timestamp."""
        self.email_verified = True
        self.email_verified_at = timezone.now()
        self.save(update_fields=['email_verified', 'email_verified_at'])
        logger.info(f"Email verified for user {self.id}")
    
    # ============================================================================
    # PASSWORD MANAGEMENT
    # ============================================================================
    
    @transaction.atomic
    def change_password(self, old_password, new_password):
        """
        Change user password with validation and history tracking.
        
        Validates:
        - Old password correctness
        - New password strength (Django validators)
        - Password reuse (last 5 passwords)
        
        Args:
            old_password: Current password for verification
            new_password: New password to set
        
        Raises:
            ValidationError: If validation fails
        """
        # Verify old password
        if not self.check_password(old_password):
            raise ValidationError(
                "Current password is incorrect",
                code='incorrect_password'
            )
        
        # Validate new password strength
        try:
            validate_password(new_password, user=self)
        except ValidationError as e:
            raise ValidationError(
                {"new_password": e.messages},
                code='weak_password'
            )
        
        # Check password history (prevent reuse)
        recent_passwords = self.password_history.only('hashed_password')[:5]
        for history in recent_passwords:
            if history.check_password(new_password):
                raise ValidationError(
                    "Cannot reuse recent passwords",
                    code='password_reused'
                )
            
        PasswordHistory.objects.create(
            user=self,
            hashed_password=self.password  # Current (old) password
        )
        
        # Set new password
        self.set_password(new_password)
        self.save(update_fields=['password'])
        
        logger.info(f"Password changed for user {self.id}")
    
    # ============================================================================
    # PRIVATE HELPER METHODS
    # ============================================================================
    
    def _cleanup_student_enrollments(self):
        """Drop all active enrollments for deactivated student."""
        from apps.academics.models import Enrollment
        
        updated = Enrollment.objects.filter(
            student=self,
            status='active'
        ).update(
            status='dropped',
            dropped_at=timezone.now()
        )
        
        if updated > 0:
            logger.info(f"Dropped {updated} enrollments for student {self.id}")
    
    def _cleanup_teacher_assignments(self):
        """Remove primary teacher status for deactivated teacher/dean."""
        from apps.academics.models import OfferingTeacher
        
        updated = OfferingTeacher.objects.filter(
            teacher=self,
            is_primary=True
        ).update(is_primary=False)
        
        if updated > 0:
            logger.warning(f"Removed primary status from {updated} offerings for {self.role} {self.id}")