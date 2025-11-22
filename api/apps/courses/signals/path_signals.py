"""
Path Publication Signals

Validates and manages path publication workflow.
"""

import logging
from django.dispatch import receiver
from django.db.models.signals import pre_save, post_save
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone

logger = logging.getLogger(__name__)


@receiver(pre_save, sender='courses.CoursePath')
def validate_publication_workflow(sender, instance, **kwargs):
    """
    Validate that path can be published only if all modules are published.
    """
    if instance.is_published and instance.pk:
        with transaction.atomic():
            original = sender.objects.select_for_update().get(pk=instance.pk)
            
            if not original.is_published and instance.is_published:
                # Check unpublished modules
                unpublished = instance.modules.filter(is_published=False).count()
                if unpublished > 0:
                    raise ValidationError(
                        f'Cannot publish path: {unpublished} unpublished modules'
                    )
                
                # Check has modules
                if not instance.modules.exists():
                    raise ValidationError('Cannot publish path: No modules defined')
                
                # Set published timestamp
                instance.published_at = timezone.now()


@receiver(post_save, sender='courses.PathModule')
def auto_publish_path_if_complete(sender, instance, created, **kwargs):
    """
    Auto-publish parent path if all modules are now published.
    """
    if not instance.is_published:
        return
    
    path = instance.path
    if path.is_published:
        return
    
    # Check if all modules published
    all_published = not path.modules.filter(is_published=False).exists()
    
    if all_published and path.modules.exists():
        path.is_published = True
        path.published_at = timezone.now()
        path.save(update_fields=['is_published', 'published_at'])
        
        logger.info(f"Auto-published path {path.id}: {path.label}")