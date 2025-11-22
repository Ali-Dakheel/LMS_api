"""
Update Timestamp Signals

Updates parent models when children change.
"""

import logging
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.utils import timezone

logger = logging.getLogger(__name__)


@receiver(post_save, sender='courses.PathModule')
def update_path_on_module_save(sender, instance, created, **kwargs):
    """Update parent path's updated_at."""
    if created:
        return
    
    instance.path.updated_at = timezone.now()
    instance.path.save(update_fields=['updated_at'])


@receiver(post_save, sender='courses.ModuleDetail')
def update_module_on_detail_save(sender, instance, created, **kwargs):
    """Update module's updated_at."""
    instance.module.updated_at = timezone.now()
    instance.module.save(update_fields=['updated_at'])


@receiver(post_save, sender='courses.Resource')
def update_module_on_resource_save(sender, instance, created, **kwargs):
    """Update module's updated_at."""
    instance.module.updated_at = timezone.now()
    instance.module.save(update_fields=['updated_at'])


@receiver(post_save, sender='courses.ModuleImage')
def update_module_on_image_save(sender, instance, created, **kwargs):
    """Update module's updated_at."""
    instance.module.updated_at = timezone.now()
    instance.module.save(update_fields=['updated_at'])