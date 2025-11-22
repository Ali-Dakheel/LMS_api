"""
File Cleanup Signals
"""

import logging
from django.dispatch import receiver
from django.db.models.signals import post_delete

logger = logging.getLogger(__name__)


@receiver(post_delete, sender='content.Book')
def cleanup_book_files(sender, instance, **kwargs):
    """Delete files when book deleted."""
    if instance.pdf_file:
        instance.pdf_file.delete(save=False)
    if instance.cover_image:
        instance.cover_image.delete(save=False)


@receiver(post_delete, sender='content.BookPage')
def cleanup_page_images(sender, instance, **kwargs):
    """Delete page images."""
    if instance.page_image:
        instance.page_image.delete(save=False)