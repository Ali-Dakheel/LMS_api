"""
Users App Signals

Auto-imports all signal handlers to ensure they're registered.

Import this in apps.py ready() method:
    from apps.users import signals
"""

from .profile_signals import (
    create_user_profile,
    log_teacher_profile_update,
    log_student_profile_update,
    log_user_deletion,
)

from .security_signals import (
    record_password_change,
    log_password_reset_token_creation,
    log_email_verification_token_creation,
)

from .counter_signals import (
    update_teacher_course_count,
    update_teacher_subject_count,
    update_student_enrollment_count,
)

__all__ = [
    # Profile signals
    'create_user_profile',
    'log_teacher_profile_update',
    'log_student_profile_update',
    'log_user_deletion',
    
    # Security signals
    'record_password_change',
    'log_password_reset_token_creation',
    'log_email_verification_token_creation',
    
    # Counter signals
    'update_teacher_course_count',
    'update_teacher_subject_count',
    'update_student_enrollment_count',
]