"""
Requirement Check Signals

Handles path requirement checking and unlocking logic.
"""

import logging
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.utils import timezone

logger = logging.getLogger(__name__)


# ============================================================================
# QUIZ REQUIREMENT SIGNALS
# ============================================================================

@receiver(post_save, sender='assessments.QuizAttempt')
def check_quiz_requirement_on_attempt(sender, instance, created, **kwargs):
    """
    Check if quiz attempt completes any path requirements.
    
    Triggered when: QuizAttempt is submitted
    """
    if instance.status == 'submitted':
        try:
            from apps.progress.models import PathRequirement, PathRequirementState
            
            # Find requirements that use this quiz
            requirements = PathRequirement.objects.filter(
                requirement_type='quiz',
                target_quiz=instance.quiz
            )
            
            for req in requirements:
                state, state_created = PathRequirementState.objects.get_or_create(
                    student=instance.student,
                    requirement=req
                )
                
                # Check if requirement is now met
                was_completed = state.is_completed()
                is_now_completed = state.check_completion()
                
                if is_now_completed and not was_completed:
                    logger.info(
                        f"✓ Requirement completed: {instance.student.email} met "
                        f"'{req.get_description()}' in '{req.path.label}'"
                    )
                
                state.attempt_count += 1
                state.last_event_at = timezone.now()
                state.save(update_fields=['attempt_count', 'last_event_at'])
            
            if requirements.exists():
                logger.debug(
                    f"Checked {requirements.count()} quiz requirements "
                    f"for {instance.student.email}"
                )
        except Exception as e:
            logger.error(
                f"Failed to check quiz requirements for attempt {instance.id}: {str(e)}",
                exc_info=True
            )


# ============================================================================
# ASSIGNMENT REQUIREMENT SIGNALS
# ============================================================================

@receiver(post_save, sender='assessments.AssignmentSubmission')
def check_assignment_requirement_on_submission(sender, instance, created, **kwargs):
    """
    Check if assignment submission completes any path requirements.
    
    Triggered when: AssignmentSubmission is graded
    """
    if instance.status == 'graded' and instance.grade is not None:
        try:
            from apps.progress.models import PathRequirement, PathRequirementState
            
            # Find requirements that use this assignment
            requirements = PathRequirement.objects.filter(
                requirement_type='assignment',
                target_assignment=instance.assignment
            )
            
            for req in requirements:
                state, state_created = PathRequirementState.objects.get_or_create(
                    student=instance.student,
                    requirement=req
                )
                
                # Check if requirement is now met
                was_completed = state.is_completed()
                is_now_completed = state.check_completion()
                
                if is_now_completed and not was_completed:
                    logger.info(
                        f"✓ Requirement completed: {instance.student.email} met "
                        f"'{req.get_description()}' in '{req.path.label}'"
                    )
                
                state.last_event_at = timezone.now()
                state.save(update_fields=['last_event_at'])
            
            if requirements.exists():
                logger.debug(
                    f"Checked {requirements.count()} assignment requirements "
                    f"for {instance.student.email}"
                )
        except Exception as e:
            logger.error(
                f"Failed to check assignment requirements for submission {instance.id}: {str(e)}",
                exc_info=True
            )


# ============================================================================
# FLASHCARD REQUIREMENT SIGNALS
# ============================================================================

@receiver(post_save, sender='assessments.FlashcardProgress')
def check_flashcard_requirement_on_review(sender, instance, created, **kwargs):
    """
    Check if flashcard review completes any path requirements.
    
    Triggered when: FlashcardProgress is updated (any review)
    """
    try:
        from apps.progress.models import PathRequirement, PathRequirementState
        
        module = instance.flashcard.module
        
        # Find requirements that use this module's flashcards
        requirements = PathRequirement.objects.filter(
            requirement_type='flashcard',
            target_module=module
        )
        
        for req in requirements:
            state, state_created = PathRequirementState.objects.get_or_create(
                student=instance.student,
                requirement=req
            )
            
            # Check if requirement is now met
            was_completed = state.is_completed()
            is_now_completed = state.check_completion()
            
            if is_now_completed and not was_completed:
                logger.info(
                    f"✓ Requirement completed: {instance.student.email} met "
                    f"'{req.get_description()}' in '{req.path.label}'"
                )
            
            state.last_event_at = timezone.now()
            state.save(update_fields=['last_event_at'])
        
        if requirements.exists():
            logger.debug(
                f"Checked {requirements.count()} flashcard requirements "
                f"for {instance.student.email}"
            )
    except Exception as e:
        logger.error(
            f"Failed to check flashcard requirements: {str(e)}",
            exc_info=True
        )


# ============================================================================
# CHAT REQUIREMENT SIGNALS
# ============================================================================

@receiver(post_save, sender='communications.ChatMessage')
def check_chat_requirement_on_message(sender, instance, created, **kwargs):
    """
    Check if chat message completes any path requirements.
    
    Triggered when: New ChatMessage is created by student
    """
    if created and instance.role == 'student':
        try:
            from apps.progress.models import PathRequirement, PathRequirementState
            
            session = instance.session
            module = session.module
            
            # Find requirements that use this module's chat
            requirements = PathRequirement.objects.filter(
                requirement_type='chat',
                target_module=module
            )
            
            for req in requirements:
                state, state_created = PathRequirementState.objects.get_or_create(
                    student=session.student,
                    requirement=req
                )
                
                # Check if requirement is now met
                was_completed = state.is_completed()
                is_now_completed = state.check_completion()
                
                if is_now_completed and not was_completed:
                    logger.info(
                        f"✓ Requirement completed: {session.student.email} met "
                        f"'{req.get_description()}' in '{req.path.label}'"
                    )
                
                state.last_event_at = timezone.now()
                state.save(update_fields=['last_event_at'])
            
            if requirements.exists():
                logger.debug(
                    f"Checked {requirements.count()} chat requirements "
                    f"for {session.student.email}"
                )
        except Exception as e:
            logger.error(
                f"Failed to check chat requirements for message {instance.id}: {str(e)}",
                exc_info=True
            )


# ============================================================================
# PATH UNLOCKING SIGNALS
# ============================================================================

@receiver(post_save, sender='progress.PathRequirementState')
def check_path_unlock_on_requirement_complete(sender, instance, created, **kwargs):
    """
    Check if completing a requirement unlocks the next path.
    
    Triggered when: PathRequirementState becomes 'completed'
    """
    if not created and instance.state == 'completed':
        try:
            from apps.progress.services import check_path_requirements, unlock_next_path
            
            path = instance.requirement.path
            student = instance.student
            
            # Check all requirements for this path
            requirements_check = check_path_requirements(student, path)
            
            if requirements_check['can_unlock_next']:
                # Attempt to unlock next path
                next_path = unlock_next_path(student, path)
                
                if next_path:
                    logger.info(
                        f"🔓 Unlocked path: '{next_path.label}' for {student.email} "
                        f"after completing '{path.label}' "
                        f"({requirements_check['overall_progress']}% mastery)"
                    )
                else:
                    logger.debug(
                        f"No next path to unlock for {student.email} "
                        f"after completing '{path.label}'"
                    )
        except Exception as e:
            logger.error(
                f"Failed to check path unlock for requirement state {instance.id}: {str(e)}",
                exc_info=True
            )


# ============================================================================
# ANALYTICS TRIGGER SIGNALS
# ============================================================================

@receiver(post_save, sender='progress.QuizAttemptSummary')
def trigger_topic_analytics_update(sender, instance, created, **kwargs):
    """
    Trigger topic analytics recalculation when quiz summary is updated.
    
    Note: Full implementation would queue a Celery task for AI analysis.
    For now, we just log that analytics should be updated.
    
    Triggered when: QuizAttemptSummary is updated
    """
    try:
        course = instance.quiz.module.path.course
        
        logger.debug(
            f"Topic analytics should be updated for {instance.student.email} "
            f"in '{course.title}' after quiz attempt (Best: {instance.best_score}%)"
        )
        
        # TODO: Queue Celery task when ai_tools app is ready
        # from apps.progress.tasks import calculate_topic_analytics_task
        # calculate_topic_analytics_task.delay(instance.student.id, course.id)
        
    except Exception as e:
        logger.error(
            f"Failed to trigger topic analytics update: {str(e)}",
            exc_info=True
        )