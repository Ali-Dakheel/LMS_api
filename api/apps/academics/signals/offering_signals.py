"""
Offering-related signals

Handles:
- Auto-generate offering slugs
"""

import logging
from django.dispatch import receiver
from django.db.models.signals import pre_save
from django.utils.text import slugify

from apps.academics.models import CourseOffering

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=CourseOffering)
def generate_offering_slug(sender, instance, **kwargs):
    """
    Auto-generate URL slug for course offerings if not provided.
    
    Format: {course-slug}-t{term_id}-s{section_id}
    Example: english-101-t5-s12
    """
    if not instance.slug:
        slug_base = f"{instance.course.slug}-t{instance.term.id}-s{instance.class_section.id}"
        instance.slug = slugify(slug_base)
        logger.debug(f"Generated slug for CourseOffering: {instance.slug}")