"""
Base Academic Models - K-12 Focus

Foundation models:
- AcademicYear: Calendar year for academic operations
"""

from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import Q, UniqueConstraint
from ..validators import AcademicYearValidator


class AcademicYear(models.Model):
    """
    Represents an academic year (calendar period for school).

    Example:
    - Name: "2024-2025"
    - Start: 2024-09-01
    - End: 2025-08-31
    - Is current: True

    Business Rules:
    - Only one academic year can be marked as current
    - Name format: YYYY-YYYY (e.g., 2024-2025)
    - Years in name must be consecutive
    - Years in name must match start_date and end_date years
    - Duration must be 300-430 days (~10-14 months)
    - End date must be after start date
    - Used for K-12 school year management
    """

    name = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Format: YYYY-YYYY (e.g., 2024-2025, must match start/end years)"
    )
    start_date = models.DateField(
        help_text="Academic year start date (e.g., 2024-09-01)"
    )
    end_date = models.DateField(
        help_text="Academic year end date (e.g., 2025-08-31)"
    )
    is_current = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Mark one academic year as current (only one allowed)"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'academic_years'
        verbose_name = 'Academic Year'
        verbose_name_plural = 'Academic Years'
        ordering = ['-start_date']
        constraints = [
            # Ensure only one academic year can be marked as current
            UniqueConstraint(
                fields=['is_current'],
                condition=Q(is_current=True),
                name='unique_current_academic_year'
            ),
        ]
        indexes = [
            models.Index(fields=['is_current']),
            models.Index(fields=['start_date']),
            models.Index(fields=['end_date']),
        ]

    def __str__(self):
        return f"{self.name} {'(Current)' if self.is_current else ''}"

    def clean(self):
        """Validate academic year configuration using validators."""
        try:
            AcademicYearValidator.validate_all(
                self.name,
                self.start_date,
                self.end_date
            )
        except ValidationError:
            raise

    def save(self, *args, **kwargs):
        """Ensure only one current academic year and run full validation."""
        self.full_clean()

        if self.is_current:
            # Set all others to False
            AcademicYear.objects.exclude(pk=self.pk).update(is_current=False)

        super().save(*args, **kwargs)

    @property
    def duration_days(self):
        """Get duration in days."""
        return (self.end_date - self.start_date).days

    @property
    def duration_months(self):
        """Get approximate duration in months."""
        return round(self.duration_days / 30.44, 1)

    @property
    def is_active(self):
        """Check if academic year is currently active."""
        from django.utils import timezone
        today = timezone.now().date()
        return self.start_date <= today <= self.end_date