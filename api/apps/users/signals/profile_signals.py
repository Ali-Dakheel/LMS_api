"""
Profile Auto-Creation Signals

Handles automatic creation of role-specific profiles:
- TeacherInfo for teachers and deans
- StudentInfo for students
- No profile for admins
"""

from typing import Any
import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import transaction, IntegrityError
from django.core.mail import mail_admins

from apps.users.models import User, TeacherInfo, StudentInfo

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def create_user_profile(sender: type[User], instance: User, created: bool, **_kwargs: Any) -> None:
    """
    Auto-create role-specific profile when user is created.

    Profiles created:
    - Teacher → TeacherInfo
    - Dean → TeacherInfo (deans can also teach)
    - Student → StudentInfo
    - Admin → No profile needed

    Features:
    - Uses get_or_create to prevent race conditions
    - Wrapped in transaction for data consistency
    - Notifies admins on unexpected errors
    """
    if not created:
        return
    
    try:
        with transaction.atomic():
            profile_created = False
            
            if instance.role == 'teacher':
                _, profile_created = TeacherInfo.objects.get_or_create(
                    user=instance
                )
                if profile_created:
                    logger.info(
                        f"Created TeacherInfo for teacher {instance.id} "
                        f"({instance.email})"
                    )

            elif instance.role == 'dean':
                # Deans can also teach, so create TeacherInfo
                _, profile_created = TeacherInfo.objects.get_or_create(
                    user=instance
                )
                if profile_created:
                    logger.info(
                        f"Created TeacherInfo for dean {instance.id} "
                        f"({instance.email})"
                    )

            elif instance.role == 'student':
                _, profile_created = StudentInfo.objects.get_or_create(
                    user=instance
                )
                if profile_created:
                    logger.info(
                        f"Created StudentInfo for student {instance.id} "
                        f"({instance.email})"
                    )

            elif instance.role == 'admin':
                # Admins don't need a profile
                logger.info(
                    f"Admin user {instance.id} ({instance.email}) "
                    f"created - no profile needed"
                )

            else:
                # Unknown role - should never happen with validation
                logger.error(
                    f"Unknown role for user {instance.id}: {instance.role}"
                )

            # Warn if profile already existed
            if not profile_created and instance.role in ['teacher', 'dean', 'student']:
                logger.warning(
                    f"Profile already existed for {instance.role} {instance.id}"
                )
    
    except IntegrityError as e:
        # Profile already exists (race condition)
        logger.warning(
            f"Profile already exists for user {instance.id} "
            f"({instance.role}): {str(e)}"
        )

    except Exception as e:
        # Unexpected error - notify admins
        logger.error(
            f"Failed to create profile for user {instance.id} "
            f"({instance.role})",
            exc_info=True
        )
        
        # Send email to admins (fail silently if email not configured)
        mail_admins(
            subject=f"User Profile Creation Failed - {instance.email}",
            message=(
                f"User ID: {instance.id}\n"
                f"Role: {instance.role}\n"
                f"Email: {instance.email}\n"
                f"Error: {str(e)}"
            ),
            fail_silently=True
        )


@receiver(post_save, sender=TeacherInfo)
def log_teacher_profile_update(sender: type[TeacherInfo], instance: TeacherInfo, created: bool, **_kwargs: Any) -> None:
    """
    Log teacher profile creation/updates for audit trail.

    Uses INFO level for creation, DEBUG for updates.
    """
    if created:
        logger.info(f"Teacher profile created for user {instance.user_id}")
    else:
        logger.debug(f"Teacher profile updated for user {instance.user_id}")


@receiver(post_save, sender=StudentInfo)
def log_student_profile_update(sender: type[StudentInfo], instance: StudentInfo, created: bool, **_kwargs: Any) -> None:
    """
    Log student profile creation/updates for audit trail.

    Uses INFO level for creation, DEBUG for updates.
    """
    if created:
        logger.info(f"Student profile created for user {instance.user_id}")
    else:
        logger.debug(f"Student profile updated for user {instance.user_id}")


@receiver(post_delete, sender=User)
def log_user_deletion(sender: type[User], instance: User, **_kwargs: Any) -> None:
    """
    Log user deletion for security audit.

    Note: TeacherInfo and StudentInfo are automatically deleted
    via CASCADE relationship.
    """
    logger.warning(
        f"User deleted: {instance.email} "
        f"(id: {instance.id}, role: {instance.role})"
    )