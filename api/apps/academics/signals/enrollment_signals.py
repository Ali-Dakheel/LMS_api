"""
Enrollment-related signals - K-12 Focus

Handles:
- Auto-enroll students when offerings are created
- Log enrollment changes
- Check section capacity
"""

import logging
from django.dispatch import receiver
from django.db import transaction
from django.db.models.signals import post_save
from django.contrib.auth import get_user_model

from apps.academics.models import CourseOffering, Enrollment

User = get_user_model()
logger = logging.getLogger(__name__)


@receiver(post_save, sender=CourseOffering)
def auto_enroll_section_students(sender, instance, created, **kwargs):
    """
    Automatically enroll students when a course offering is created (K-12).

    Enrollment strategy determined by CourseOffering.auto_enroll:
    - 'none': No auto-enrollment
    - 'section': Enroll students in the same class section

    Excludes inactive users.
    """
    if not created or instance.auto_enroll == 'none':
        return

    try:
        with transaction.atomic():
            students = User.objects.none()

            if instance.auto_enroll == 'section':
                # K-12: Enroll students in this class section
                students = User.objects.filter(
                    section_assignments__class_section=instance.class_section,
                    is_active=True,
                ).distinct()
            else:
                logger.warning(
                    f"CourseOffering {instance.id} has unknown auto_enroll value: "
                    f"{instance.auto_enroll}. Valid values: 'none', 'section'"
                )
                return
            
            # Create enrollments in bulk with capacity check
            enrollments_to_create = []
            existing_students = set(
                Enrollment.objects.filter(offering=instance).values_list(
                    'student_id', flat=True
                )
            )

            # Get capacity and current enrollment count
            capacity = instance.effective_capacity
            current_count = Enrollment.objects.filter(
                offering=instance,
                status__in=['active', 'pending']
            ).count()

            for student in students:
                if student.id not in existing_students:
                    # Check if we have capacity
                    if current_count + len(enrollments_to_create) < capacity:
                        enrollments_to_create.append(
                            Enrollment(
                                student=student,
                                offering=instance,
                                status='active'
                            )
                        )
                    else:
                        logger.warning(
                            f"Capacity reached for {instance.course.title} "
                            f"({instance.class_section.name}). "
                            f"Student {student.email} not auto-enrolled."
                        )

            if enrollments_to_create:
                created_count = len(enrollments_to_create)
                Enrollment.objects.bulk_create(
                    enrollments_to_create,
                    ignore_conflicts=True,
                    batch_size=1000
                )
                logger.info(
                    f"Auto-enrolled {created_count} students in "
                    f"{instance.course.title} ({instance.class_section.name})"
                )
    
    except Exception as e:
        logger.error(
            f"Error auto-enrolling students for offering {instance.id}: {str(e)}"
        )


@receiver(post_save, sender=Enrollment)
def log_enrollment_change(sender, instance, created, **kwargs):
    """Log enrollment changes for audit trail."""
    if created:
        logger.info(
            f"New enrollment: {instance.student.email} → "
            f"{instance.offering.course.title} ({instance.offering.class_section.name}) "
            f"[Status: {instance.status}]"
        )
    else:
        # Log updates (status changes are tracked by update_fields if used)
        update_fields = kwargs.get('update_fields', None)
        if update_fields and 'status' in update_fields:
            logger.info(
                f"Enrollment status updated: {instance.student.email} → "
                f"{instance.offering.course.title} "
                f"[New status: {instance.status}]"
            )


@receiver(post_save, sender=Enrollment)
def check_section_capacity(sender, instance, created, **kwargs):
    """Check if section is over capacity (warning, not blocking)."""
    if not created or instance.status != 'active':
        return
    
    offering = instance.offering
    capacity = offering.effective_capacity
    
    active_count = Enrollment.objects.filter(
        offering=offering,
        status='active'
    ).count()
    
    if active_count > capacity:
        logger.warning(
            f"Section overflow: {offering.class_section.name} has "
            f"{active_count} active students but capacity is {capacity}"
        )