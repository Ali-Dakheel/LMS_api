"""
BookTOCItem Model
"""

from django.db import models
from django.utils.text import slugify


class BookTOCItem(models.Model):
    """
    Hierarchical table of contents entry.
    """
    
    LEVEL_CHOICES = [
        (1, 'Chapter'),
        (2, 'Section'),
        (3, 'Subsection'),
        (4, 'Sub-subsection'),
        (5, 'Sub-sub-subsection'),
    ]
    
    book = models.ForeignKey('content.Book', on_delete=models.CASCADE, related_name='toc_items', db_index=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children', db_index=True)
    
    level = models.PositiveIntegerField(choices=LEVEL_CHOICES)
    title = models.CharField(max_length=500)
    
    # Page mapping
    start_page = models.PositiveIntegerField()
    end_page = models.PositiveIntegerField()
    
    slug = models.SlugField()
    order = models.PositiveIntegerField(default=0)
    
    # AI-generated
    summary = models.TextField(blank=True)
    keywords = models.CharField(max_length=500, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'book_toc_items'
        verbose_name = 'Book TOC Item'
        verbose_name_plural = 'Book TOC Items'
        unique_together = ['book', 'slug']
        ordering = ['book', 'level', 'order']
        indexes = [
            models.Index(fields=['book', 'parent']),
            models.Index(fields=['book', 'level']),
            models.Index(fields=['start_page', 'end_page']),
        ]
    
    def __str__(self):
        indent = "  " * (self.level - 1)
        return f"{indent}{self.title} (pp. {self.start_page}-{self.end_page})"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)