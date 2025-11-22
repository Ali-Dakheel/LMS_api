"""
Module Models

PathModule, ModulePackage, ModuleDetail, ModuleImage
"""

from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.db.models import UniqueConstraint

from .managers import PathModuleManager, ModulePackageManager


class PathModule(models.Model):
    """
    Module within a learning path.
    
    Contains:
    - Title, category, description
    - Content details (ModuleDetail)
    - Resources (Resource)
    - Images (ModuleImage)
    - Publishing status
    """
    
    objects = PathModuleManager()
    
    path = models.ForeignKey(
        'courses.CoursePath',
        on_delete=models.CASCADE,
        related_name='modules',
        db_index=True
    )
    
    title = models.CharField(max_length=255)
    slug = models.SlugField()
    category = models.CharField(max_length=100, db_index=True)
    description = models.TextField(blank=True)
    outcomes = models.TextField(blank=True)
    
    order = models.PositiveIntegerField(default=0)
    
    is_published = models.BooleanField(default=False, db_index=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'path_modules'
        verbose_name = 'Path Module'
        verbose_name_plural = 'Path Modules'
        constraints = [
            UniqueConstraint(
                fields=['path', 'slug'],
                name='unique_module_slug_per_path'
            ),
            UniqueConstraint(
                fields=['path', 'title'],
                name='unique_module_title_per_path'
            ),
        ]
        ordering = ['path', 'order']
        indexes = [
            models.Index(fields=['is_published']),
            models.Index(fields=['category']),
        ]
    
    def __str__(self):
        return f"{self.path.label} - {self.title}"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)


class ModulePackage(models.Model):
    """
    Grouping of related modules.
    
    Example: "Parts of Speech" package contains "Nouns", "Verbs", "Adjectives"
    """
    
    objects = ModulePackageManager()
    
    module = models.ForeignKey(
        PathModule,
        on_delete=models.CASCADE,
        related_name='packages',
        db_index=True
    )
    
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'module_packages'
        verbose_name = 'Module Package'
        verbose_name_plural = 'Module Packages'
        ordering = ['module', 'order']
    
    def __str__(self):
        return f"{self.module.title} - {self.title}"


class ModuleDetail(models.Model):
    """
    Detailed content of a module.
    
    Content types:
    - Rich text (HTML)
    - PDF file
    - HTML
    """
    
    CONTENT_TYPE_CHOICES = [
        ('text', 'Rich Text'),
        ('pdf', 'PDF File'),
        ('html', 'HTML'),
    ]
    
    module = models.OneToOneField(
        PathModule,
        on_delete=models.CASCADE,
        related_name='detail'
    )
    
    content_type = models.CharField(
        max_length=20,
        choices=CONTENT_TYPE_CHOICES,
        default='text'
    )
    
    text_content = models.TextField(blank=True, help_text="HTML-formatted text")
    pdf_file = models.FileField(upload_to='module_pdfs/', null=True, blank=True)
    
    objectives = models.TextField(blank=True)
    
    is_ai_generated = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'module_details'
        verbose_name = 'Module Detail'
        verbose_name_plural = 'Module Details'
    
    def __str__(self):
        return f"Detail for {self.module.title}"
    
    def clean(self):
        """Ensure at least one content type provided."""
        if not self.text_content and not self.pdf_file:
            raise ValidationError(
                _('Module must have text content or PDF file')
            )


class ModuleImage(models.Model):
    """
    Images/illustrations for modules.
    """
    
    module = models.ForeignKey(
        PathModule,
        on_delete=models.CASCADE,
        related_name='images'
    )
    
    title = models.CharField(max_length=255)
    image = models.ImageField(upload_to='module_images/')
    alt_text = models.CharField(max_length=255, blank=True)
    
    order = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'module_images'
        verbose_name = 'Module Image'
        verbose_name_plural = 'Module Images'
        ordering = ['module', 'order']
    
    def __str__(self):
        return f"{self.module.title} - {self.title}"