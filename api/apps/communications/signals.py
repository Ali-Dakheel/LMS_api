"""
Communications App Signals

Handles:
- Session metric updates
- Auto-title generation
- Notice publication tracking
"""

import logging
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.utils import timezone

logger = logging.getLogger(__name__)


@receiver(post_save, sender='communications.ChatMessage')
def update_session_metrics_on_message(sender, instance, created, **kwargs):
    """
    Update session metrics when a message is added.
    
    Updates:
    - total_messages count
    - last_message_at timestamp
    """
    if created:
        session = instance.session
        
        # Update total messages (if not already updated by add_message method)
        # This is a safety net
        actual_count = session.messages.count()
        if session.total_messages != actual_count:
            session.total_messages = actual_count
            session.last_message_at = instance.timestamp
            session.save(update_fields=['total_messages', 'last_message_at'])


@receiver(post_save, sender='communications.ChatMessage')
def auto_generate_session_title(sender, instance, created, **kwargs):
    """
    Auto-generate session title from first student message.
    """
    if created and instance.is_from_student():
        session = instance.session
        
        # Only generate if session title is still default
        if session.title == "New Chat Session":
            from apps.communications.services import generate_session_title
            
            session.title = generate_session_title(instance.content)
            session.save(update_fields=['title'])
            
            logger.debug(f"Auto-generated title for session {session.id}: {session.title}")


@receiver(post_save, sender='communications.Notice')
def track_notice_publication(sender, instance, created, **kwargs):
    """
    Track when notice is published.
    """
    if not created and instance.is_published and not instance.published_at:
        instance.published_at = timezone.now()
        instance.save(update_fields=['published_at'])
        
        logger.info(f"Notice {instance.id} published: {instance.title}")


@receiver(post_save, sender='communications.ChatSession')
def log_session_completion(sender, instance, created, **kwargs):
    """
    Log when chat session is marked as completed.
    """
    if not created and instance.status == 'completed':
        logger.info(
            f"Chat session {instance.id} completed: "
            f"{instance.total_messages} messages, "
            f"{instance.student.name} in {instance.module.title}"
        )