"""
Resource Models

Resource, ModuleToolOverride
"""

from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .managers import ResourceManager


class Resource(models.Model):
    """
    Resources linked to modules.
    
    Types: PDF, PPTX, DOCX, URL
    """
    
    objects = ResourceManager()
    
    TYPE_CHOICES = [
        ('pdf', 'PDF Document'),
        ('pptx', 'PowerPoint'),
        ('docx', 'Word Document'),
        ('url', 'External Link'),
    ]
    
    module = models.ForeignKey(
        'courses.PathModule',
        on_delete=models.CASCADE,
        related_name='resources'
    )
    
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, db_index=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    file = models.FileField(upload_to='resources/', null=True, blank=True)
    url = models.URLField(null=True, blank=True, unique=True) 
    
    order = models.PositiveIntegerField(default=0)
    is_required = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'resources'
        verbose_name = 'Resource'
        verbose_name_plural = 'Resources'
        ordering = ['module', 'order']
        indexes = [
            models.Index(fields=['type']),
            models.Index(fields=['is_required']),
            models.Index(fields=['url']), 
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['module', 'type', 'title'],
                name='unique_resource_per_module'
            )
        ]
    
    def __str__(self):
        return f"{self.module.title} - {self.title}"
    
    def clean(self):
        """Validate file/url consistency."""
        if self.type in ['pdf', 'pptx', 'docx']:
            if not self.file:
                raise ValidationError({'file': _('File required for this type')})
            if self.url:
                raise ValidationError({'url': _('URL should not be set for file types')})
        
        if self.type == 'url':
            if not self.url:
                raise ValidationError({'url': _('URL required for external links')})
            if self.file:
                raise ValidationError({'file': _('File should not be set for URLs')})


class ModuleToolOverride(models.Model):
    """
    Override subject-level tool settings at module level.
    
    Example: Subject has simulations enabled, but specific module disables them.
    """
    
    module = models.OneToOneField(
        'courses.PathModule',
        on_delete=models.CASCADE,
        related_name='tool_override'
    )
    
    # Override flags (None = use subject default)
    ppt_generator = models.BooleanField(null=True, blank=True)
    flashcard_creator = models.BooleanField(null=True, blank=True)
    quiz_generator = models.BooleanField(null=True, blank=True)
    lesson_plan_generator = models.BooleanField(null=True, blank=True)
    worksheet_generator = models.BooleanField(null=True, blank=True)
    mind_map_generator = models.BooleanField(null=True, blank=True)
    simulation = models.BooleanField(null=True, blank=True)
    practice_problems = models.BooleanField(null=True, blank=True)
    step_by_step_solver = models.BooleanField(null=True, blank=True)
    
    # Student visibility
    flashcard_student_visible = models.BooleanField(default=True)
    quiz_student_visible = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'module_tool_overrides'
        verbose_name = 'Module Tool Override'
        verbose_name_plural = 'Module Tool Overrides'
    
    def __str__(self):
        return f"Tool Override - {self.module.title}"