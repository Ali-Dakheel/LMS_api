"""
CoursePath Model

Learning paths with 4 scopes: course, teacher, student, offering
"""

from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.db.models import Q, UniqueConstraint
from django.contrib.auth import get_user_model

from .managers import CoursePathManager

User = get_user_model()


class CoursePath(models.Model):
    """
    Learning path within a course.
    
    Scopes:
    - course: Visible to all students
    - teacher: Teacher's personal prep
    - student: Personalized remedial path
    - offering: Section-specific content
    
    Weekly structure with objectives, outcomes, and modules.
    """
    
    objects = CoursePathManager()
    
    SCOPE_CHOICES = [
        ('course', 'Course (All Students)'),
        ('teacher', "Teacher's Prep"),
        ('student', 'Student (Personal)'),
        ('offering', 'Offering (Section Specific)'),
    ]
    
    GENERATION_STATUS_CHOICES = [
        ('not_generated', 'Not Generated'),
        ('partial', 'Partial'),
        ('complete', 'Complete'),
    ]
    
    SOURCE_KIND_CHOICES = [
        ('spec', 'From Specification'),
        ('book', 'From Book'),
        ('manual', 'Manual Entry'),
    ]
    
    # Core relationships
    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.CASCADE,
        related_name='paths',
        db_index=True
    )
    
    scope = models.CharField(
        max_length=20,
        choices=SCOPE_CHOICES,
        default='course',
        db_index=True
    )
    
    # Scope-specific fields
    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='teacher_paths',
        null=True,
        blank=True,
        limit_choices_to={'role': 'teacher'},
        db_index=True
    )
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='student_paths',
        null=True,
        blank=True,
        limit_choices_to={'role': 'student'},
        db_index=True
    )
    offering = models.ForeignKey(
        'academics.CourseOffering',
        on_delete=models.CASCADE,
        related_name='paths',
        null=True,
        blank=True,
        db_index=True
    )
    
    # Path content
    label = models.CharField(max_length=255, help_text="e.g., Week 1: Introduction")
    slug = models.SlugField()
    description = models.TextField(blank=True)
    objectives = models.TextField(blank=True, help_text="Learning objectives")
    outcomes = models.TextField(blank=True, help_text="Learning outcomes mapped to CILOs")
    
    # Dates
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    
    # Source tracking
    source_kind = models.CharField(
        max_length=20,
        choices=SOURCE_KIND_CHOICES,
        default='manual'
    )
    source_book = models.ForeignKey(
        'content.Book',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='course_paths'
    )
    source_toc_item = models.ForeignKey(
        'content.BookTOCItem',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    # AI generation
    generation_status = models.CharField(
        max_length=20,
        choices=GENERATION_STATUS_CHOICES,
        default='not_generated',
        db_index=True
    )
    
    # Publishing
    is_published = models.BooleanField(default=False, db_index=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    order = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'course_paths'
        verbose_name = 'Course Path'
        verbose_name_plural = 'Course Paths'
        constraints = [
            UniqueConstraint(
                fields=['course', 'scope'],
                condition=Q(scope='course'),
                name='unique_course_path_per_course'
            ),
            UniqueConstraint(
                fields=['course', 'scope', 'teacher'],
                condition=Q(scope='teacher'),
                name='unique_teacher_path_per_course'
            ),
            UniqueConstraint(
                fields=['course', 'scope', 'student'],
                condition=Q(scope='student'),
                name='unique_student_path_per_course'
            ),
            UniqueConstraint(
                fields=['offering', 'scope'],
                condition=Q(scope='offering'),
                name='unique_offering_path'
            ),
        ]
        ordering = ['course', 'order']
        indexes = [
            models.Index(fields=['is_published']),
            models.Index(fields=['generation_status']),
            models.Index(fields=['scope']),
            models.Index(fields=['course', 'scope']),
            models.Index(fields=['teacher', 'scope']),
            models.Index(fields=['student', 'scope']),
            models.Index(fields=['offering']),
        ]
    
    def __str__(self):
        scope_str = ""
        if self.teacher:
            scope_str = f" - {self.teacher.name}'s Prep"
        elif self.student:
            scope_str = f" - {self.student.name}'s Personal"
        elif self.offering:
            scope_str = f" - {self.offering.class_section.name}"
        
        return f"{self.label}{scope_str}"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.label)
        
        self.full_clean()
        super().save(*args, **kwargs)
    
    def clean(self):
        """Validate dates and scope consistency."""
        errors = {}
        
        # Validate dates
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                errors['end_date'] = _('End date must be after start date')
        
        # Validate path dates within term (offering scope)
        if self.scope == 'offering' and self.offering:
            term = self.offering.term
            if self.start_date and self.start_date < term.start_date:
                errors['start_date'] = _('Start date must be after term start')
            if self.end_date and self.end_date > term.end_date:
                errors['end_date'] = _('End date must be before term end')
        
        # Validate scope fields
        if self.scope == 'teacher' and not self.teacher:
            errors['teacher'] = _('Teacher required for teacher scope')
        if self.scope == 'student' and not self.student:
            errors['student'] = _('Student required for student scope')
        if self.scope == 'offering' and not self.offering:
            errors['offering'] = _('Offering required for offering scope')
        
        if errors:
            raise ValidationError(errors)