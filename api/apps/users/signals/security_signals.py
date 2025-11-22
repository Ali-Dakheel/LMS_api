"""
Security & Password Tracking Signals

Handles:
- Password change tracking
- Password history recording
- Token creation logging
"""

import logging
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from apps.users.models import User, PasswordHistory

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=User)
def record_password_change(sender, instance, **kwargs):
    """
    Track password changes for security auditing.
    
    Records OLD password to history before it's changed.
    """
    if not instance.pk:
        return  # Skip on user creation
    
    try:
        old_instance = User.objects.get(pk=instance.pk)
        
        # Only process if password actually changed
        if old_instance.password != instance.password:
            PasswordHistory.objects.create(
                user=old_instance,
                hashed_password=old_instance.password 
            )
            logger.info(f"Password history recorded for user {instance.id}")
    
    except User.DoesNotExist:
        pass  # User doesn't exist yet
    except Exception as e:
        logger.error(f"Error recording password change: {str(e)}")

@receiver(post_save, sender='users.PasswordResetToken')
def log_password_reset_token_creation(sender, instance, created, **kwargs):
    """
    Log password reset token creation for security monitoring.
    
    Helps track:
    - Frequency of password reset requests
    - Potential account takeover attempts
    """
    if created:
        logger.debug(
            f" Password reset token created for user {instance.user.id} "
            f"(expires: {instance.expires_at})"
        )


@receiver(post_save, sender='users.EmailVerificationToken')
def log_email_verification_token_creation(sender, instance, created, **kwargs):
    """
    Log email verification token creation.
    
    Tracks email verification attempts.
    """
    if created:
        logger.debug(
            f" Email verification token created for user {instance.user.id} "
            f"(expires: {instance.expires_at})"
        )