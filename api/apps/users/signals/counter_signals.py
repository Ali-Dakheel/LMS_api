"""
Denormalized Counter Update Signals

Maintains accurate counts in TeacherInfo and StudentInfo:
- Teacher course count
- Teacher subject count
- Student enrollment count

Updates happen automatically when related objects change.
"""

import logging
from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from django.core.mail import mail_admins

logger = logging.getLogger(__name__)


@receiver(post_save, sender='academics.OfferingTeacher')
@receiver(post_delete, sender='academics.OfferingTeacher')
def update_teacher_course_count(sender, instance, **kwargs):
    """
    Update teacher's course count when course offerings change.
    
    Triggers:
    - OfferingTeacher created (teacher assigned to offering)
    - OfferingTeacher deleted (teacher removed from offering)
    
    Updates:
    - TeacherInfo.courses_count
    """
    try:

        try:
            teacher_info = instance.teacher.teacher_info
        except instance.teacher._meta.get_field('teacher_info').related_model.DoesNotExist:
            logger.warning(f"Teacher {instance.teacher.id} has no TeacherInfo profile")
            return
        # Count active offerings taught by this teacher
        course_count = instance.teacher.taught_offerings.count()
        
        teacher_info.courses_count = course_count
        teacher_info.save(update_fields=['courses_count'])

        logger.debug(
            f"Updated course count for teacher {instance.teacher.id}: "
            f"{course_count} courses"
        )

    except Exception as e:
        logger.error(
            f"Error updating teacher course count: {str(e)}",
            exc_info=True
        )
        # Notify admins for critical data integrity issues
        mail_admins(
            subject=f"Signal Failure: Teacher Course Count Update",
            message=f"Teacher ID: {instance.teacher_id}\nError: {str(e)}",
            fail_silently=True
        )


@receiver(m2m_changed, sender='academics.TeacherSubject') # TODO: check here later
def update_teacher_subject_count(sender, instance, action, **kwargs):
    """
    Update teacher's subject count when subject assignments change.
    
    Triggers (M2M changes):
    - post_add: Subject(s) assigned to teacher
    - post_remove: Subject(s) removed from teacher
    - post_clear: All subjects cleared
    
    Updates:
    - TeacherInfo.subjects_count
    
    Note: instance is the Teacher (User) with related subjects
    """
    # Only update on actual changes
    if action not in ['post_add', 'post_remove', 'post_clear']:
        return
    
    try:
        teacher_info = instance.teacher_info
        
        # Count assigned subjects
        subject_count = instance.subject_assignments.count()
        
        teacher_info.subjects_count = subject_count
        teacher_info.save(update_fields=['subjects_count'])

        logger.debug(
            f"Updated subject count for teacher {instance.id}: "
            f"{subject_count} subjects"
        )

    except Exception as e:
        logger.error(
            f"Error updating subject count for teacher {instance.id}: {str(e)}",
            exc_info=True
        )
        # Notify admins for critical data integrity issues
        mail_admins(
            subject=f"Signal Failure: Teacher Subject Count Update",
            message=f"Teacher ID: {instance.id}\nError: {str(e)}",
            fail_silently=True
        )


@receiver(post_save, sender='academics.Enrollment')
@receiver(post_delete, sender='academics.Enrollment')
def update_student_enrollment_count(sender, instance, **kwargs):
    """
    Update student's enrollment count when enrollments change.
    
    Triggers:
    - Enrollment created (student enrolls in course)
    - Enrollment deleted (student drops/withdraws)
    - Enrollment status changed (via post_save)
    
    Updates:
    - StudentInfo.enrolled_courses_count (only active enrollments)
    """
    try:
        student_info = instance.student.student_info
        
        # Count only ACTIVE enrollments
        enrollment_count = instance.student.enrollments.filter(
            status='active'
        ).count()
        
        student_info.enrolled_courses_count = enrollment_count
        student_info.save(update_fields=['enrolled_courses_count'])

        logger.debug(
            f"Updated enrollment count for student {instance.student.id}: "
            f"{enrollment_count} active courses"
        )

    except Exception as e:
        logger.error(
            f"Error updating student enrollment count: {str(e)}",
            exc_info=True
        )
        # Notify admins for critical data integrity issues
        mail_admins(
            subject=f"Signal Failure: Student Enrollment Count Update",
            message=f"Student ID: {instance.student_id}\nError: {str(e)}",
            fail_silently=True
        )