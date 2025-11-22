"""
Subject Model

Represents academic subjects with tool configurations.
"""

from django.db import models
from .managers import SubjectManager


class Subject(models.Model):
    """
    Academic subject with AI tool configurations.
    
    Examples: Mathematics, English, Computer Science
    
    Tool flags control which AI tools are available for this subject.
    """
    
    objects = SubjectManager()
    
    LEVEL_CHOICES = [
        ('SCHOOL', 'School (K-12)'),
        ('UNIV', 'University'),
    ]
    
    name = models.CharField(max_length=255, db_index=True)
    code = models.CharField(max_length=20, unique=True, db_index=True)
    description = models.TextField(blank=True)
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES, db_index=True)
    
    # Tool availability
    ppt_generator = models.BooleanField(default=True)
    flashcard_creator = models.BooleanField(default=True)
    quiz_generator = models.BooleanField(default=True)
    lesson_plan_generator = models.BooleanField(default=True)
    worksheet_generator = models.BooleanField(default=True)
    mind_map_generator = models.BooleanField(default=True)
    simulation = models.BooleanField(default=False)
    practice_problems = models.BooleanField(default=False)
    step_by_step_solver = models.BooleanField(default=False)
    
    # Teacher-only restrictions
    ppt_generator_teacher_only = models.BooleanField(default=False)
    flashcard_creator_teacher_only = models.BooleanField(default=False)
    quiz_generator_teacher_only = models.BooleanField(default=False)
    
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'subjects'
        verbose_name = 'Subject'
        verbose_name_plural = 'Subjects'
        ordering = ['name']
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['level']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.code})"