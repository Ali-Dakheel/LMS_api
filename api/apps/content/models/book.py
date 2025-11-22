"""
Book and BookPage Models
"""

from django.db import models
from django.core.validators import FileExtensionValidator
from django.contrib.auth import get_user_model

from .managers import BookManager

User = get_user_model()


class Book(models.Model):
    """
    Textbook PDF with metadata and processing status.
    """
    
    objects = BookManager()
    
    STATUS_CHOICES = [
        ('pending', 'Pending Processing'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('error', 'Error'),
    ]
    
    # Metadata
    title = models.CharField(max_length=255, db_index=True)
    author = models.CharField(max_length=255, blank=True)
    isbn = models.CharField(max_length=20, blank=True, unique=True, null=True, db_index=True)
    publication_year = models.IntegerField(null=True, blank=True)
    description = models.TextField(blank=True)
    
    # File
    pdf_file = models.FileField(
        upload_to='books/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])]
    )
    file_size = models.BigIntegerField(help_text="File size in bytes")
    
    # Cover
    cover_image = models.ImageField(upload_to='book_covers/', null=True, blank=True)
    
    # Processing
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    total_pages = models.PositiveIntegerField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    keywords = models.TextField(blank=True)
    
    # Publishing
    is_published = models.BooleanField(default=False, db_index=True)
    
    # Relationships
    courses = models.ManyToManyField('courses.Course', related_name='textbooks', blank=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='uploaded_books')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processing_started_at = models.DateTimeField(null=True, blank=True)
    processing_completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'books'
        verbose_name = 'Book'
        verbose_name_plural = 'Books'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['is_published']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} by {self.author}"
    
    def save(self, *args, **kwargs):
        if self.pdf_file:
            self.file_size = self.pdf_file.size
        super().save(*args, **kwargs)


class BookPage(models.Model):
    """
    Individual page from a book with OCR.
    """
    
    OCR_STATUS_CHOICES = [
        ('pending', 'Pending OCR'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='pages', db_index=True)
    page_number = models.PositiveIntegerField()
    
    # Content
    page_image = models.ImageField(upload_to='book_pages/')
    extracted_text = models.TextField(blank=True)
    
    # OCR
    ocr_status = models.CharField(max_length=20, choices=OCR_STATUS_CHOICES, default='pending', db_index=True)
    ocr_confidence = models.FloatField(null=True, blank=True, help_text="0-1 confidence score")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    ocr_completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'book_pages'
        verbose_name = 'Book Page'
        verbose_name_plural = 'Book Pages'
        unique_together = ['book', 'page_number']
        ordering = ['book', 'page_number']
        indexes = [
            models.Index(fields=['book', 'page_number']),
            models.Index(fields=['ocr_status']),
        ]
    
    def __str__(self):
        return f"{self.book.title} - Page {self.page_number}"