"""
BookAnalysisJob Model
"""

from django.db import models
from .managers import BookAnalysisJobManager


class BookAnalysisJob(models.Model):
    """
    Tracks async PDF processing jobs.
    """
    
    objects = BookAnalysisJobManager()
    
    JOB_TYPE_CHOICES = [
        ('text_extraction', 'Text Extraction'),
        ('ocr', 'OCR Processing'),
        ('cover_extraction', 'Cover Image'),
        ('toc_extraction', 'TOC Extraction'),
        ('full_processing', 'Full Processing'),
    ]
    
    STATUS_CHOICES = [
        ('queued', 'Queued'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('retrying', 'Retrying'),
    ]
    
    book = models.ForeignKey('content.Book', on_delete=models.CASCADE, related_name='analysis_jobs', db_index=True)
    job_type = models.CharField(max_length=30, choices=JOB_TYPE_CHOICES, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='queued', db_index=True)
    
    # Celery
    celery_task_id = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    
    # Progress
    progress_percent = models.PositiveIntegerField(default=0)
    total_items = models.PositiveIntegerField(null=True, blank=True)
    processed_items = models.PositiveIntegerField(default=0)
    
    # Error handling
    error_message = models.TextField(blank=True)
    retry_count = models.PositiveIntegerField(default=0)
    max_retries = models.PositiveIntegerField(default=3)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'book_analysis_jobs'
        verbose_name = 'Book Analysis Job'
        verbose_name_plural = 'Book Analysis Jobs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['book', 'status']),
            models.Index(fields=['status']),
            models.Index(fields=['celery_task_id']),
        ]
    
    def __str__(self):
        return f"{self.get_job_type_display()} - {self.book.title} ({self.get_status_display()})"