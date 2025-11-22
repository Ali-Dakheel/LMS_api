"""
Token Models - Password reset and email verification

Security features:
- SHA256 hashed tokens (never store plaintext)
- One-time use enforcement
- Automatic expiration
- Rate limiting
"""

from typing import Optional, Tuple, TYPE_CHECKING
from django.db import models, transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
import hashlib
import secrets
from datetime import timedelta
import logging

if TYPE_CHECKING:
    from .user import User

logger = logging.getLogger(__name__)

# Rate limiting constants
PASSWORD_RESET_RATE_LIMIT = 3  # requests per window
PASSWORD_RESET_RATE_WINDOW_MINUTES = 5

# Token expiration constants
PASSWORD_RESET_TOKEN_EXPIRY_HOURS = 24
EMAIL_VERIFICATION_TOKEN_EXPIRY_HOURS = 48


class PasswordResetToken(models.Model):
    """
    One-time password reset tokens with 24-hour expiration.
    
    Security:
    - Tokens hashed with SHA256 before storage
    - Rate limited (3 requests per 5 minutes)
    - Previous tokens invalidated on new request
    - Automatic expiration after 24 hours
    """
    
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='reset_tokens'
    )
    token = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text="SHA256 hashed token"
    )
    expires_at = models.DateTimeField(db_index=True)
    used = models.BooleanField(default=False, db_index=True)
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'password_reset_tokens'
        verbose_name_plural = 'Password Reset Tokens'
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['user', 'used']),
            models.Index(fields=['user', 'created_at']),
        ]
    
    def __str__(self) -> str:
        """String representation showing status."""
        if self.used:
            return f"Reset token for {self.user.email} (used)"
        elif self.expires_at < timezone.now():
            return f"Reset token for {self.user.email} (expired)"
        else:
            return f"Reset token for {self.user.email} (valid)"

    def is_valid(self) -> bool:
        """Check if token is valid (not expired and not used)."""
        return not self.used and self.expires_at > timezone.now()

    def mark_used(self) -> None:
        """Mark token as used with timestamp."""
        self.used = True
        self.used_at = timezone.now()
        self.save(update_fields=['used', 'used_at'])

    @staticmethod
    def create_token(user: 'User') -> Tuple[str, 'PasswordResetToken']:
        """
        Create a new password reset token.
        
        Features:
        - Rate limits: Max 3 requests per 5 minutes
        - Invalidates previous unused tokens
        - Returns raw token (for email) and token object
        
        Args:
            user: User requesting password reset
        
        Returns:
            tuple: (raw_token, token_object)
        
        Raises:
            ValidationError: If rate limit exceeded
        """
        # Rate limit check
        recent_tokens = PasswordResetToken.objects.filter(
            user=user,
            created_at__gte=timezone.now() - timedelta(minutes=PASSWORD_RESET_RATE_WINDOW_MINUTES)
        ).count()

        if recent_tokens >= PASSWORD_RESET_RATE_LIMIT:
            raise ValidationError(
                "Too many password reset requests. Please try again later.",
                code='rate_limit_exceeded'
            )

        # Delete old unused tokens
        PasswordResetToken.objects.filter(user=user, used=False).delete()

        # Generate secure token
        raw_token = secrets.token_urlsafe(32)
        hashed_token = hashlib.sha256(raw_token.encode()).hexdigest()

        # Create token in database
        token = PasswordResetToken.objects.create(
            user=user,
            token=hashed_token,
            expires_at=timezone.now() + timedelta(hours=PASSWORD_RESET_TOKEN_EXPIRY_HOURS)
        )
        
        logger.info(f"Password reset token created for user {user.id}")
        return raw_token, token
    
    @staticmethod
    def verify_token(raw_token: str) -> Optional['PasswordResetToken']:
        """
        Verify and retrieve a password reset token.

        Args:
            raw_token: Raw token string from email

        Returns:
            PasswordResetToken or None if invalid/expired
        """
        hashed_token = hashlib.sha256(raw_token.encode()).hexdigest()
        token = PasswordResetToken.objects.filter(token=hashed_token).first()

        if token and token.is_valid():
            return token

        return None


class EmailVerificationTokenQuerySet(models.QuerySet):
    """Custom QuerySet for EmailVerificationToken."""
    
    def valid_only(self):
        """Filter only valid (not expired, not used) tokens."""
        return self.filter(
            used=False,
            expires_at__gt=timezone.now()
        )
    
    def for_user(self, user):
        """Filter tokens for specific user."""
        return self.filter(user=user)


class EmailVerificationTokenManager(models.Manager):
    """Custom manager for EmailVerificationToken."""
    
    def get_queryset(self):
        return EmailVerificationTokenQuerySet(self.model, using=self._db)
    
    def valid_only(self):
        return self.get_queryset().valid_only()
    
    def for_user(self, user):
        return self.get_queryset().for_user(user)


class EmailVerificationToken(models.Model):
    """
    One-time email verification tokens with 48-hour expiration.
    
    Features:
    - SHA256 hashed storage
    - 48-hour validity period
    - Custom manager with validation methods
    """
    
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='email_verification_tokens'
    )
    token = models.CharField(
        max_length=255,
        unique=True,
        db_index=True
    )
    expires_at = models.DateTimeField(db_index=True)
    used = models.BooleanField(default=False, db_index=True)
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    objects = EmailVerificationTokenManager()
    
    class Meta:
        db_table = 'email_verification_tokens'
        verbose_name_plural = 'Email Verification Tokens'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['user', 'used']),
        ]
    
    def __str__(self) -> str:
        status = "used" if self.used else "valid" if self.is_valid() else "expired"
        return f"Email verification for {self.user.email} ({status})"

    def is_valid(self) -> bool:
        """Check if token is still valid."""
        return not self.used and self.expires_at > timezone.now()

    def mark_used(self) -> None:
        """Mark token as used with timestamp."""
        self.used = True
        self.used_at = timezone.now()
        self.save(update_fields=['used', 'used_at'])

    @staticmethod
    def create_token(user: 'User') -> Tuple[str, 'EmailVerificationToken']:
        """
        Create email verification token.
        
        Invalidates previous unused tokens before creating new one.
        
        Args:
            user: User to verify
        
        Returns:
            tuple: (raw_token, token_object)
        """
        # Delete previous verification tokens
        EmailVerificationToken.objects.filter(
            user=user,
            used=False
        ).delete()
        
        # Generate token
        raw_token = secrets.token_urlsafe(32)
        hashed_token = hashlib.sha256(raw_token.encode()).hexdigest()

        # Create in database
        token = EmailVerificationToken.objects.create(
            user=user,
            token=hashed_token,
            expires_at=timezone.now() + timedelta(hours=EMAIL_VERIFICATION_TOKEN_EXPIRY_HOURS)
        )
        
        logger.info(f"Email verification token created for user {user.id}")
        return raw_token, token
    
    @staticmethod
    def verify_token(raw_token: str) -> Optional['EmailVerificationToken']:
        """
        Verify email token and return token object.

        Args:
            raw_token: Raw token from email

        Returns:
            EmailVerificationToken or None if invalid
        """
        hashed_token = hashlib.sha256(raw_token.encode()).hexdigest()
        token = EmailVerificationToken.objects.filter(
            token=hashed_token
        ).first()

        if token and token.is_valid():
            return token

        return None


@transaction.atomic
def verify_email_via_token(raw_token: str) -> 'User':
    """
    Verify user email using token.
    
    Performs atomic transaction:
    1. Validates token
    2. Marks user email as verified
    3. Marks token as used
    
    Args:
        raw_token: Raw token string from email
    
    Returns:
        User: User with verified email
    
    Raises:
        ValidationError: If token is invalid or expired
    """
    token = EmailVerificationToken.verify_token(raw_token)
    
    if not token:
        raise ValidationError(
            "Invalid or expired verification token",
            code='invalid_token'
        )
    
    user = token.user
    user.email_verified = True
    user.email_verified_at = timezone.now()
    user.save(update_fields=['email_verified', 'email_verified_at'])

    token.mark_used()

    logger.info(f"Email verified for user {user.id}")
    return user