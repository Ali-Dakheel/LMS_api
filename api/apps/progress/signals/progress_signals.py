"""
Progress Update Signals

Handles automatic progress updates when students interact with content.
"""

import logging
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.utils import timezone

logger = logging.getLogger(__name__)


# ============================================================================
# LESSON PROGRESS SIGNALS
# ============================================================================

@receiver(post_save, sender='progress.LessonProgress')
def update_path_progress_on_lesson_complete(sender, instance, created, **kwargs):
    """
    Update learning path progress when a lesson is completed.
    
    Triggered when: LessonProgress.is_completed changes to True
    """
    if instance.is_completed:
        try:
            from apps.progress.services import update_path_progress
            
            path = instance.module.path
            update_path_progress(instance.student, path)
            
            logger.debug(
                f"Updated path progress for {instance.student.email} "
                f"in '{path.label}' after completing '{instance.module.title}'"
            )
        except Exception as e:
            logger.error(
                f"Failed to update path progress for lesson {instance.id}: {str(e)}",
                exc_info=True
            )


# ============================================================================
# QUIZ ATTEMPT SIGNALS
# ============================================================================

@receiver(post_save, sender='assessments.QuizAttempt')
def update_quiz_summary_on_attempt(sender, instance, created, **kwargs):
    """
    Update quiz attempt summary when a quiz is submitted.
    
    Triggered when: QuizAttempt.status becomes 'submitted'
    """
    if instance.status == 'submitted':
        try:
            from apps.progress.services import update_quiz_summary
            
            update_quiz_summary(instance.student, instance.quiz, instance)
            
            logger.debug(
                f"Updated quiz summary for {instance.student.email} - "
                f"{instance.quiz.title} (Score: {instance.score}%)"
            )
        except Exception as e:
            logger.error(
                f"Failed to update quiz summary for attempt {instance.id}: {str(e)}",
                exc_info=True
            )


# ============================================================================
# FLASHCARD PROGRESS SIGNALS
# ============================================================================

@receiver(post_save, sender='assessments.FlashcardProgress')
def update_flashcard_set_progress_on_review(sender, instance, created, **kwargs):
    """
    Update flashcard set progress when individual flashcard is reviewed.
    
    Triggered when: FlashcardProgress is saved (any review)
    """
    try:
        from apps.progress.services import update_flashcard_set_progress
        
        module = instance.flashcard.module
        update_flashcard_set_progress(instance.student, module)
        
        logger.debug(
            f"Updated flashcard set progress for {instance.student.email} "
            f"in '{module.title}' (Ease: {instance.ease_factor})"
        )
    except Exception as e:
        logger.error(
            f"Failed to update flashcard set progress: {str(e)}",
            exc_info=True
        )


# ============================================================================
# ASSIGNMENT SUBMISSION SIGNALS
# ============================================================================

@receiver(post_save, sender='assessments.AssignmentSubmission')
def update_assignment_progress_on_submission(sender, instance, created, **kwargs):
    """
    Update assignment progress when submission is created or updated.
    
    Triggered when: AssignmentSubmission is saved
    """
    try:
        from apps.progress.services import update_assignment_progress
        
        update_assignment_progress(instance.student, instance.assignment, instance)
        
        logger.debug(
            f"Updated assignment progress for {instance.student.email} - "
            f"{instance.assignment.title} (Status: {instance.status})"
        )
    except Exception as e:
        logger.error(
            f"Failed to update assignment progress for submission {instance.id}: {str(e)}",
            exc_info=True
        )


# ============================================================================
# CHAT MESSAGE SIGNALS
# ============================================================================

@receiver(post_save, sender='communications.ChatMessage')
def update_chat_metrics_on_message(sender, instance, created, **kwargs):
    """
    Update chat metrics when a message is sent.
    
    Triggered when: New ChatMessage is created
    """
    if created:
        try:
            from apps.progress.services import update_chat_metrics
            
            session = instance.session
            module = session.module
            student = session.student
            
            update_chat_metrics(student, module)
            
            logger.debug(
                f"Updated chat metrics for {student.email} in '{module.title}'"
            )
        except Exception as e:
            logger.error(
                f"Failed to update chat metrics for message {instance.id}: {str(e)}",
                exc_info=True
            )


# ============================================================================
# PATH COMPLETION LOGGING
# ============================================================================

@receiver(post_save, sender='progress.LearningPathProgress')
def log_path_completion(sender, instance, created, **kwargs):
    """
    Log when a learning path is completed.
    
    Triggered when: LearningPathProgress.status becomes 'completed'
    """
    if not created and instance.status == 'completed' and instance.completed_at:
        logger.info(
            f"🎉 Path completed: {instance.student.email} finished "
            f"'{instance.path.label}' ({instance.completion_percentage}%)"
        )