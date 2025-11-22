"""
Learning Path Progress Models
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.contrib.auth import get_user_model
from decimal import Decimal

from .managers import LearningPathProgressManager

User = get_user_model()


class LearningPathProgress(models.Model):
    """Student progress through learning paths."""
    
    objects = LearningPathProgressManager()
    
    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('locked', 'Locked'),
    ]
    
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='path_progress', db_index=True)
    path = models.ForeignKey('courses.CoursePath', on_delete=models.CASCADE, related_name='student_progress', db_index=True)
    
    completion_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'), validators=[MinValueValidator(0), MaxValueValidator(100)])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started', db_index=True)
    
    last_step_key = models.CharField(max_length=255, blank=True)
    progress_index = models.PositiveIntegerField(default=0)
    
    completed_at = models.DateTimeField(null=True, blank=True)
    
    is_unlocked = models.BooleanField(default=True, db_index=True)
    unlocked_at = models.DateTimeField(null=True, blank=True)
    
    started_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'learning_path_progress'
        verbose_name = 'Learning Path Progress'
        verbose_name_plural = 'Learning Path Progress'
        unique_together = ['student', 'path']
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.student.name} - {self.path.label} ({self.completion_percentage}%)"
    
    def update_completion(self):
        """Update completion from modules."""
        from apps.progress.models import LessonProgress
        
        modules = self.path.modules.filter(is_published=True)
        total = modules.count()
        
        if total == 0:
            self.completion_percentage = Decimal('0.00')
        else:
            completed = LessonProgress.objects.filter(
                student=self.student,
                module__in=modules,
                is_completed=True
            ).count()
            
            self.completion_percentage = round((Decimal(completed) / Decimal(total)) * Decimal('100.00'), 2)
        
        # Update status
        if self.completion_percentage >= 100:
            self.status = 'completed'
            if not self.completed_at:
                self.completed_at = timezone.now()
        elif self.completion_percentage > 0:
            self.status = 'in_progress'
        
        self.save()
    
    def unlock(self):
        if not self.is_unlocked:
            self.is_unlocked = True
            self.unlocked_at = timezone.now()
            self.save(update_fields=['is_unlocked', 'unlocked_at'])