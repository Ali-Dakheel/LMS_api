"""
Worksheet Model
"""

from django.db import models
from django.core.validators import FileExtensionValidator
from django.contrib.auth import get_user_model

User = get_user_model()


class Worksheet(models.Model):
    """AI-generated worksheet PDFs."""
    
    DIFFICULTY_CHOICES = [('easy', 'Easy'), ('medium', 'Medium'), ('hard', 'Hard')]
    
    module = models.ForeignKey('courses.PathModule', on_delete=models.CASCADE, related_name='worksheets', db_index=True)
    
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    topic = models.CharField(max_length=255)
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='medium')
    grade_level = models.CharField(max_length=50, blank=True)
    
    worksheet_file = models.FileField(upload_to='worksheets/', validators=[FileExtensionValidator(['pdf'])])
    answer_key_file = models.FileField(upload_to='worksheets/answers/', null=True, blank=True, validators=[FileExtensionValidator(['pdf'])])
    
    is_ai_generated = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_worksheets')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'worksheets'
        verbose_name = 'Worksheet'
        verbose_name_plural = 'Worksheets'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.module.title})"