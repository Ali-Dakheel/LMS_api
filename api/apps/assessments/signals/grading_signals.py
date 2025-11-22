"""
Grading and Tracking Signals
"""

import logging
from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save
from django.utils import timezone

logger = logging.getLogger(__name__)


@receiver(post_save, sender='assessments.QuizAttempt')
def auto_grade_quiz_on_submission(sender, instance, created, **kwargs):
    """
    Auto-grade quiz when attempt is submitted.
    """
    if instance.status == 'submitted' and not instance.score:
        from apps.assessments.services import grade_quiz_attempt
        
        try:
            results = grade_quiz_attempt(instance)
            logger.info(
                f"Auto-graded quiz attempt {instance.id}: "
                f"Score {results['score']}%, "
                f"{results['correct_count']}/{results['total_questions']} correct"
            )
        except Exception as e:
            logger.error(
                f"Failed to auto-grade quiz attempt {instance.id}: {str(e)}",
                exc_info=True
            )


@receiver(post_save, sender='assessments.AssignmentSubmission')
def track_submission_timestamp(sender, instance, **kwargs):
    """
    Track submission timestamp when status changes to submitted.
    """
    if instance.status in ['submitted', 'graded', 'returned'] and not instance.submitted_at:
        instance.submitted_at = timezone.now()
        instance.save(update_fields=['submitted_at'])
        
        logger.info(
            f"Assignment submission {instance.id} timestamp recorded for "
            f"{instance.student.email}"
        )


@receiver(post_save, sender='assessments.Assignment')
def log_assignment_publication(sender, instance, created, **kwargs):
    """
    Log when assignment is published.
    """
    if not created:
        try:
            old = sender.objects.get(pk=instance.pk)
            if not old.is_published and instance.is_published:
                if not instance.published_at:
                    instance.published_at = timezone.now()
                    instance.save(update_fields=['published_at'])
                
                logger.info(f"Assignment {instance.id} published: {instance.title}")
        except sender.DoesNotExist:
            pass


@receiver(post_save, sender='assessments.Quiz')
def log_quiz_publication(sender, instance, created, **kwargs):
    """
    Log when quiz is published.
    """
    if not created:
        try:
            old = sender.objects.get(pk=instance.pk)
            if not old.is_published and instance.is_published:
                if not instance.published_at:
                    instance.published_at = timezone.now()
                    instance.save(update_fields=['published_at'])
                
                logger.info(f"Quiz {instance.id} published: {instance.title}")
        except sender.DoesNotExist:
            pass


@receiver(post_save, sender='assessments.FlashcardProgress')
def log_flashcard_mastery(sender, instance, created, **kwargs):
    """
    Log when flashcard is mastered.
    """
    if not created and instance.is_mastered:
        logger.debug(
            f"Flashcard mastered: Student {instance.student.id}, "
            f"Card {instance.flashcard.id}, "
            f"Ease: {instance.ease_factor}, "
            f"Interval: {instance.interval_days} days"
        )


@receiver(post_save, sender='assessments.AssignmentSubmission')
def log_late_submission(sender, instance, created, **kwargs):
    """
    Log late submissions for tracking.
    """
    if instance.status == 'submitted' and instance.submitted_at:
        if instance.is_late():
            late_by = instance.submitted_at - instance.assignment.due_date
            logger.warning(
                f"Late submission: {instance.student.email} submitted "
                f"{instance.assignment.title} {late_by.days} days late"
            )