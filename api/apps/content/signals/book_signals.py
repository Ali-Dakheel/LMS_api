"""
Book Processing Signals
"""

import logging
from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save
from django.utils import timezone

logger = logging.getLogger(__name__)


@receiver(post_save, sender='content.Book')
def trigger_book_processing(sender, instance, created, **kwargs):
    """Trigger processing on book upload."""
    if created and instance.status == 'pending':
        from apps.content.models import BookAnalysisJob
        
        job = BookAnalysisJob.objects.create(
            book=instance,
            job_type='full_processing',
            status='queued',
            total_items=1
        )
        
        logger.info(f"Created processing job {job.id} for book {instance.id}")


@receiver(post_save, sender='content.BookAnalysisJob')
def update_book_status_on_job_completion(sender, instance, **kwargs):
    """Update book status when job completes."""
    if instance.status == 'completed' and instance.book.status != 'completed':
        instance.book.status = 'completed'
        instance.book.processing_completed_at = timezone.now()
        instance.book.save(update_fields=['status', 'processing_completed_at'])
    
    elif instance.status == 'failed' and instance.book.status != 'error':
        instance.book.status = 'error'
        instance.book.error_message = instance.error_message
        instance.book.save(update_fields=['status', 'error_message'])


@receiver(pre_save, sender='content.Book')
def track_processing_start(sender, instance, **kwargs):
    """Track processing start time."""
    if instance.pk:
        try:
            old = sender.objects.get(pk=instance.pk)
            if old.status == 'pending' and instance.status == 'processing':
                instance.processing_started_at = timezone.now()
        except sender.DoesNotExist:
            pass