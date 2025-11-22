import logging
from django.utils import timezone
from django.db.models import Avg, Count, Sum, Q, F
from decimal import Decimal

logger = logging.getLogger(__name__)

def check_path_requirements(student, path):
    """
    Check all requirements for a path and update states.
    
    Args:
        student: User instance
        path: CoursePath instance
    
    Returns:
        dict: {
            'completed_count': int,
            'total_count': int,
            'mandatory_completed': bool,
            'overall_progress': Decimal,
            'can_unlock_next': bool
        }
    """
    from apps.progress.models import PathRequirement, PathRequirementState
    
    requirements = PathRequirement.objects.for_path(path)
    
    if not requirements.exists():
        return {
            'completed_count': 0,
            'total_count': 0,
            'mandatory_completed': True,
            'overall_progress': Decimal('100.00'),
            'can_unlock_next': True
        }
    
    completed_count = 0
    total_weight = 0
    completed_weight = 0
    mandatory_completed = True
    
    for req in requirements:
        # Get or create state
        state, created = PathRequirementState.objects.get_or_create(
            student=student,
            requirement=req
        )
        
        # Check completion
        is_complete = state.check_completion()
        
        if is_complete:
            completed_count += 1
            completed_weight += req.weight
        elif req.is_mandatory:
            mandatory_completed = False
        
        total_weight += req.weight
    
    # Calculate overall progress
    if total_weight > 0:
        overall_progress = (Decimal(completed_weight) / Decimal(total_weight)) * Decimal('100.00')
    else:
        overall_progress = Decimal('0.00')
    
    # Check if can unlock next path (80% mastery + mandatory requirements)
    can_unlock_next = (overall_progress >= 80 and mandatory_completed)
    
    return {
        'completed_count': completed_count,
        'total_count': requirements.count(),
        'mandatory_completed': mandatory_completed,
        'overall_progress': round(overall_progress, 2),
        'can_unlock_next': can_unlock_next
    }


def unlock_next_path(student, current_path):
    """
    Unlock the next sequential path if requirements are met.
    
    Args:
        student: User instance
        current_path: CoursePath instance
    
    Returns:
        CoursePath or None: Next path if unlocked, None otherwise
    """
    from apps.progress.models import LearningPathProgress
    
    # Check current path requirements
    requirements_check = check_path_requirements(student, current_path)
    
    if not requirements_check['can_unlock_next']:
        logger.debug(f"Cannot unlock next path: requirements not met")
        return None
    
    # Find next path in sequence
    next_path = current_path.course.paths.filter(
        order__gt=current_path.order,
        scope='course',
        is_published=True
    ).order_by('order').first()
    
    if not next_path:
        logger.debug(f"No next path to unlock")
        return None
    
    # Get or create progress for next path
    next_progress, created = LearningPathProgress.objects.get_or_create(
        student=student,
        path=next_path
    )
    
    # Unlock if locked
    if not next_progress.is_unlocked:
        next_progress.unlock()
        logger.info(f"Unlocked path {next_path.label} for {student.email}")
    
    return next_path

