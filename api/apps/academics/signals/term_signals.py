"""
Term-related signals - K-12 Focus

Handles:
- Validate term dates within academic year
"""

import logging
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from apps.academics.models import Term

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Term)
def validate_term_within_academic_year(sender, instance, created, **kwargs):
    """
    Validate that term dates don't exceed academic year dates.
    
    Note: This is a safety check. Primary validation happens in Term.clean().
    
    Raises:
        ValidationError: If term dates are outside academic year bounds
    """
    if instance.start_date < instance.academic_year.start_date:
        error_msg = (
            f'Term {instance.id} start_date {instance.start_date} is before '
            f'academic year start_date {instance.academic_year.start_date}'
        )
        logger.error(error_msg)
        raise ValidationError(
            _('Term cannot start before academic year start date')
        )
    
    if instance.end_date > instance.academic_year.end_date:
        error_msg = (
            f'Term {instance.id} end_date {instance.end_date} is after '
            f'academic year end_date {instance.academic_year.end_date}'
        )
        logger.error(error_msg)
        raise ValidationError(
            _('Term cannot end after academic year end date')
        )