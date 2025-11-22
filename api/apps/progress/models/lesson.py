"""
Lesson Progress Models
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.contrib.auth import get_user_model
from decimal import Decimal

from .managers import LessonProgressManager

User = get_user_model()


class LessonProgress(models.Model):
    """Student progress through individual modules."""
    
    objects = LessonProgressManager()
    
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lesson_progress', db_index=True)
    module = models.ForeignKey('courses.PathModule', on_delete=models.CASCADE, related_name='student_progress', db_index=True)
    
    completion_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'), validators=[MinValueValidator(0), MaxValueValidator(100)])
    is_completed = models.BooleanField(default=False, db_index=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    time_spent_seconds = models.PositiveIntegerField(default=0)
    view_count = models.PositiveIntegerField(default=0)
    last_accessed_at = models.DateTimeField(auto_now=True, db_index=True)
    
    progress_data = models.JSONField(default=dict, blank=True)
    
    started_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'lesson_progress'
        verbose_name = 'Lesson Progress'
        verbose_name_plural = 'Lesson Progress'
        unique_together = ['student', 'module']
        ordering = ['-last_accessed_at']
        indexes = [
            models.Index(fields=['student', 'is_completed']),
            models.Index(fields=['module', 'is_completed']),
        ]
    
    def __str__(self):
        return f"{self.student.name} - {self.module.title} ({self.completion_percentage}%)"
    
    def mark_completed(self):
        if not self.is_completed:
            self.is_completed = True
            self.completion_percentage = Decimal('100.00')
            self.completed_at = timezone.now()
            self.save(update_fields=['is_completed', 'completion_percentage', 'completed_at'])
    
    def add_time_spent(self, seconds):
        self.time_spent_seconds += seconds
        self.save(update_fields=['time_spent_seconds'])
    
    def increment_view_count(self):
        self.view_count += 1
        self.save(update_fields=['view_count'])