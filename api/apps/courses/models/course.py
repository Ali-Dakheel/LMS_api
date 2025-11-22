"""
Course Model

Represents courses within subjects.
"""

from django.db import models
from django.utils.text import slugify
from .managers import CourseManager


class Course(models.Model):
    """
    Course within a subject.
    
    Examples: English 101, Data Structures, Mathematics Grade 5
    """
    
    objects = CourseManager()
    
    subject = models.ForeignKey(
        'courses.Subject',
        on_delete=models.CASCADE,
        related_name='courses',
        db_index=True
    )
    
    title = models.CharField(max_length=255, db_index=True)
    code = models.CharField(max_length=20, unique=True, db_index=True)
    slug = models.SlugField(unique=True, db_index=True)
    description = models.TextField(blank=True)
    outcomes = models.TextField(blank=True, help_text="Course learning outcomes")
    
    level = models.CharField(
        max_length=10,
        choices=[('SCHOOL', 'School'), ('UNIV', 'University')],
        db_index=True
    )
    credit_hours = models.PositiveIntegerField(null=True, blank=True)
    
    # Syllabus
    syllabus_file = models.FileField(upload_to='syllabus/', null=True, blank=True)
    syllabus_analysis_status = models.CharField(
        max_length=20,
        choices=[
            ('not_analyzed', 'Not Analyzed'),
            ('analyzing', 'Analyzing'),
            ('analyzed', 'Analyzed'),
            ('error', 'Error'),
        ],
        default='not_analyzed',
        db_index=True
    )
    
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'courses'
        verbose_name = 'Course'
        verbose_name_plural = 'Courses'
        ordering = ['code']
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['subject', 'level']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.code})"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)