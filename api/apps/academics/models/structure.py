"""
Academic Structure Models - K-12 Focus

Organizational units:
- Term: K-12 grade levels (Grade 1-12)
- ClassSection: Physical classroom sections (e.g., Grade 5-A)
"""

from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.db.models import UniqueConstraint
from django.contrib.auth import get_user_model

from .base import AcademicYear

User = get_user_model()


class Term(models.Model):
    """
    Represents a K-12 grade level within an academic year.

    For K-12:
    - Type: GRADE (Grade 1, Grade 2, ..., Grade 12)
    - Duration: Full academic year
    - Represents the grade level, not a semester

    Example:
    - Grade 5 for 2024-2025 academic year
    - Grade 10 for 2024-2025 academic year

    Business Rules:
    - Unique per academic_year + number
    - Grade numbers: 1-12 only
    - Term dates must be within academic year
    - Only one current grade per number (e.g., only one "Grade 5" marked as current)
    """

    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.PROTECT,
        related_name='terms',
        db_index=True,
        help_text="Academic year this grade belongs to"
    )

    # Grade number: 1-12
    number = models.PositiveIntegerField(
        help_text="Grade number (1-12)"
    )

    name = models.CharField(
        max_length=255,
        help_text="e.g., Grade 5, Grade 10"
    )

    start_date = models.DateField(
        help_text="Grade start date (usually same as academic year start)"
    )
    end_date = models.DateField(
        help_text="Grade end date (usually same as academic year end)"
    )

    is_current = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Mark if this grade is currently active"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'terms'
        verbose_name = 'Term (Grade)'
        verbose_name_plural = 'Terms (Grades)'
        # Ensure uniqueness per academic year + number
        constraints = [
            UniqueConstraint(
                fields=['academic_year', 'number'],
                name='unique_grade_per_academic_year'
            ),
        ]
        ordering = ['academic_year', 'number']
        indexes = [
            models.Index(fields=['is_current']),
            models.Index(fields=['academic_year', 'number']),
        ]

    def __str__(self):
        return f"{self.name} ({self.academic_year.name})"

    def clean(self):
        """Validate grade configuration."""
        errors = {}

        # Validate dates
        if self.start_date and self.end_date:
            if self.start_date >= self.end_date:
                errors['end_date'] = _('End date must be after start date')

            # Check if dates are within academic year
            if self.academic_year_id:
                if (self.start_date < self.academic_year.start_date or
                    self.end_date > self.academic_year.end_date):
                    errors['start_date'] = _('Term dates must be within academic year')

        # Validate grade numbers (1-12)
        if self.number < 1 or self.number > 12:
            errors['number'] = _('Grade number must be between 1 and 12')

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        """Ensure only one current grade per number."""
        self.full_clean()

        if self.is_current:
            # Only one current term per grade number across all academic years
            Term.objects.filter(
                number=self.number,
                is_current=True
            ).exclude(pk=self.pk).update(is_current=False)

        super().save(*args, **kwargs)

    @property
    def duration_days(self):
        """Get term duration in days."""
        return (self.end_date - self.start_date).days

    @property
    def is_active_now(self):
        """Check if term is currently active."""
        from django.utils import timezone
        today = timezone.now().date()
        return self.start_date <= today <= self.end_date


class ClassSection(models.Model):
    """
    Represents a K-12 classroom section.

    For K-12:
    - Grade 5-A, Grade 10-B, Grade 12-C
    - Associated with term (grade level)
    - Has homeroom teacher
    - Typical capacity: 20-40 students

    Example:
    - Grade 5-A with 30 students, homeroom teacher: Ms. Smith
    - Grade 10-B with 25 students, homeroom teacher: Mr. Johnson

    Business Rules:
    - Unique per term (grade) and section name
    - Capacity must be positive (1-50 students)
    - Each section has exactly one homeroom teacher
    """

    term = models.ForeignKey(
        Term,
        on_delete=models.CASCADE,
        related_name='class_sections',
        db_index=True,
        help_text="Grade level (1-12)"
    )

    section = models.CharField(
        max_length=10,
        db_index=True,
        help_text="Section identifier (A, B, C, etc.)"
    )

    name = models.CharField(
        max_length=255,
        help_text="e.g., Grade 5-A, Grade 10-B"
    )

    homeroom_teacher = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='homeroom_classes',
        limit_choices_to={'role': 'teacher'},
        help_text="Homeroom teacher for this section"
    )

    capacity = models.PositiveIntegerField(
        default=30,
        help_text="Maximum students in this section (typically 20-40)"
    )

    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Mark section as active/inactive"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'class_sections'
        verbose_name = 'Class Section'
        verbose_name_plural = 'Class Sections'
        # K-12: unique per term (grade) and section
        constraints = [
            UniqueConstraint(
                fields=['term', 'section'],
                name='unique_k12_section'
            ),
        ]
        ordering = ['term', 'section']
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['term', 'section']),
        ]

    def __str__(self):
        return self.name

    def clean(self):
        """Validate section configuration."""
        errors = {}

        # Validate capacity (1-50 students)
        if self.capacity < 1:
            errors['capacity'] = _('Capacity must be at least 1')
        elif self.capacity > 50:
            errors['capacity'] = _('Capacity cannot exceed 50 students')

        if errors:
            raise ValidationError(errors)