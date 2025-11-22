import logging
from django.utils import timezone
from django.db.models import Avg, Count, Sum, Q, F
from decimal import Decimal

logger = logging.getLogger(__name__)


# ============================================================================
# PROGRESS CALCULATION SERVICES
# ============================================================================

def update_lesson_progress(student, module, completion_delta=0, time_spent=0):
    """
    Update or create lesson progress for a student.
    
    Args:
        student: User instance
        module: PathModule instance
        completion_delta: Change in completion % (can be negative)
        time_spent: Seconds spent (to add)
    
    Returns:
        LessonProgress instance
    """
    from apps.progress.models import LessonProgress
    
    progress, created = LessonProgress.objects.get_or_create(
        student=student,
        module=module,
        defaults={'completion_percentage': Decimal('0.00')}
    )
    
    if not created:
        # Update existing progress
        if completion_delta != 0:
            new_completion = progress.completion_percentage + Decimal(str(completion_delta))
            progress.completion_percentage = max(
                Decimal('0.00'),
                min(Decimal('100.00'), new_completion)
            )
        
        if time_spent > 0:
            progress.add_time_spent(time_spent)
        
        # Check completion
        if progress.completion_percentage >= 100 and not progress.is_completed:
            progress.mark_completed()
        
        progress.increment_view_count()
    
    return progress


def update_path_progress(student, path):
    """
    Update learning path progress by calculating from modules.
    
    Args:
        student: User instance
        path: CoursePath instance
    
    Returns:
        LearningPathProgress instance
    """
    from apps.progress.models import LearningPathProgress
    
    progress, created = LearningPathProgress.objects.get_or_create(
        student=student,
        path=path
    )
    
    progress.update_completion()
    
    return progress


def update_quiz_summary(student, quiz, attempt):
    """
    Update quiz attempt summary from a completed attempt.
    
    Args:
        student: User instance
        quiz: Quiz instance
        attempt: QuizAttempt instance
    
    Returns:
        QuizAttemptSummary instance
    """
    from apps.progress.models import QuizAttemptSummary
    
    summary, created = QuizAttemptSummary.objects.get_or_create(
        student=student,
        quiz=quiz
    )
    
    summary.update_from_attempt(attempt)
    
    logger.debug(f"Updated quiz summary for {student.email} - {quiz.title}")
    
    return summary


def update_flashcard_set_progress(student, module):
    """
    Update flashcard set progress from individual flashcard progress.
    
    Args:
        student: User instance
        module: PathModule instance
    
    Returns:
        FlashcardSetProgress instance
    """
    from apps.progress.models import FlashcardSetProgress
    
    progress, created = FlashcardSetProgress.objects.get_or_create(
        student=student,
        module=module
    )
    
    progress.calculate_progress()
    
    return progress


def update_assignment_progress(student, assignment, submission):
    """
    Update assignment progress from submission.
    
    Args:
        student: User instance
        assignment: Assignment instance
        submission: AssignmentSubmission instance
    
    Returns:
        AssignmentProgress instance
    """
    from apps.progress.models import AssignmentProgress
    
    progress, created = AssignmentProgress.objects.get_or_create(
        student=student,
        assignment=assignment
    )
    
    progress.update_from_submission(submission)
    
    return progress


def update_chat_metrics(student, module):
    """
    Update chat session metrics from chat sessions.
    
    Args:
        student: User instance
        module: PathModule instance
    
    Returns:
        ChatSessionMetric instance
    """
    from apps.progress.models import ChatSessionMetric
    
    metric, created = ChatSessionMetric.objects.get_or_create(
        student=student,
        module=module
    )
    
    metric.calculate_metrics()
    
    return metric
