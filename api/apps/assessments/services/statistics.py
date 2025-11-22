"""
Assessment Statistics Calculations
"""

import logging
from typing import Dict, Any
from django.db import models
from django.utils import timezone

logger = logging.getLogger(__name__)


def calculate_assignment_statistics(assignment) -> Dict[str, Any]:
    """
    Calculate statistics for an assignment.
    
    Args:
        assignment: Assignment instance
    
    Returns:
        dict: {
            'total_students': int,
            'submitted_count': int,
            'graded_count': int,
            'late_count': int,
            'submission_rate': float,
            'grading_rate': float,
            'average_grade': float
        }
    """
    from apps.assessments.models import AssignmentSubmission
    
    submissions = AssignmentSubmission.objects.filter(assignment=assignment)
    
    total_students = submissions.count()
    submitted_count = submissions.filter(
        status__in=['submitted', 'graded', 'returned']
    ).count()
    graded_count = submissions.filter(
        status__in=['graded', 'returned']
    ).count()
    late_count = submissions.filter(
        submitted_at__gt=assignment.due_date
    ).count()
    
    # Average grade
    graded_submissions = submissions.filter(
        status__in=['graded', 'returned'],
        grade__isnull=False
    )
    avg_grade = graded_submissions.aggregate(
        avg=models.Avg('grade')
    )['avg'] or 0
    
    # Rates
    submission_rate = (submitted_count / total_students * 100) if total_students > 0 else 0
    grading_rate = (graded_count / submitted_count * 100) if submitted_count > 0 else 0
    
    return {
        'total_students': total_students,
        'submitted_count': submitted_count,
        'graded_count': graded_count,
        'late_count': late_count,
        'submission_rate': round(submission_rate, 1),
        'grading_rate': round(grading_rate, 1),
        'average_grade': round(avg_grade, 1)
    }


def calculate_flashcard_mastery(student, module) -> Dict[str, Any]:
    """
    Calculate student's flashcard mastery for a module.
    
    Args:
        student: User instance (student)
        module: PathModule instance
    
    Returns:
        dict: {
            'total_cards': int,
            'mastered_cards': int,
            'mastery_percentage': float,
            'due_for_review': int
        }
    """
    from apps.assessments.models import Flashcard, FlashcardProgress
    
    total_cards = Flashcard.objects.filter(
        module=module,
        is_active=True
    ).count()
    
    if total_cards == 0:
        return {
            'total_cards': 0,
            'mastered_cards': 0,
            'mastery_percentage': 0,
            'due_for_review': 0
        }
    
    progress_records = FlashcardProgress.objects.filter(
        student=student,
        flashcard__module=module,
        flashcard__is_active=True
    )
    
    mastered_cards = progress_records.filter(is_mastered=True).count()
    due_for_review = progress_records.filter(
        next_review_at__lte=timezone.now()
    ).count()
    
    mastery_percentage = (mastered_cards / total_cards * 100) if total_cards > 0 else 0
    
    return {
        'total_cards': total_cards,
        'mastered_cards': mastered_cards,
        'mastery_percentage': round(mastery_percentage, 1),
        'due_for_review': due_for_review
    }