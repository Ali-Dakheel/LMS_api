"""
Academic Year Validators

Business logic for AcademicYear validation (framework-agnostic).
Used by models, serializers, admin, and CLI.
"""

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import re


class AcademicYearValidator:
    """Business logic for AcademicYear validation (framework-agnostic)"""
    
    MIN_YEAR = 2000
    MAX_YEAR = 2100
    NAME_PATTERN = r'^\d{4}-\d{4}$'
    MIN_DURATION_DAYS = 300
    MAX_DURATION_DAYS = 430
    
    @staticmethod
    def validate_name(name):
        """
        Validate name format and year values.
        
        Rules:
        - Format: YYYY-YYYY
        - Years must be consecutive (e.g., 2024-2025, not 2024-2026)
        - Years must be between MIN_YEAR and MAX_YEAR
        
        Args:
            name (str): Academic year name
            
        Raises:
            ValidationError: If name is invalid
        """
        if not name or not isinstance(name, str):
            raise ValidationError(
                _('Name is required and must be a string'),
                code='invalid_type',
            )
        
        if not re.match(AcademicYearValidator.NAME_PATTERN, name):
            raise ValidationError(
                _(
                    f'Name must be in format YYYY-YYYY (e.g., 2024-2025). '
                    f'Got: {name}'
                ),
                code='invalid_format',
            )
        
        try:
            start_year, end_year = map(int, name.split('-'))
        except (ValueError, IndexError):
            raise ValidationError(
                _('Invalid name format'),
                code='invalid_format',
            )
        
        # Validate year range
        if start_year < AcademicYearValidator.MIN_YEAR or start_year > AcademicYearValidator.MAX_YEAR:
            raise ValidationError(
                _(
                    f'Start year must be between {AcademicYearValidator.MIN_YEAR} '
                    f'and {AcademicYearValidator.MAX_YEAR}. Got: {start_year}'
                ),
                code='year_out_of_range',
            )
        
        if end_year < AcademicYearValidator.MIN_YEAR or end_year > AcademicYearValidator.MAX_YEAR:
            raise ValidationError(
                _(
                    f'End year must be between {AcademicYearValidator.MIN_YEAR} '
                    f'and {AcademicYearValidator.MAX_YEAR}. Got: {end_year}'
                ),
                code='year_out_of_range',
            )
        
        # Years must be consecutive
        if end_year - start_year != 1:
            raise ValidationError(
                _(
                    f'Years must be consecutive (span exactly 1 year). '
                    f'Got {end_year - start_year} years. Use format like 2024-2025'
                ),
                code='invalid_span',
            )
        
        if end_year <= start_year:
            raise ValidationError(
                _('End year must be greater than start year'),
                code='invalid_order',
            )
        
        return True
    
    @staticmethod
    def validate_dates(name, start_date, end_date):
        """
        Validate date configuration.
        
        Rules:
        - Start date year must match name start year
        - End date year must match name end year
        - End date must be after start date
        - Duration must be between MIN_DURATION_DAYS and MAX_DURATION_DAYS
        
        Args:
            name (str): Academic year name (e.g., "2024-2025")
            start_date (date): Academic year start date
            end_date (date): Academic year end date
            
        Raises:
            ValidationError: If dates are invalid
        """
        if not start_date:
            raise ValidationError(
                {'start_date': _('Start date is required')},
                code='missing_start_date',
            )
        
        if not end_date:
            raise ValidationError(
                {'end_date': _('End date is required')},
                code='missing_end_date',
            )
        
        try:
            name_start_year, name_end_year = map(int, name.split('-'))
        except (ValueError, IndexError):
            raise ValidationError(
                _('Invalid name format'),
                code='invalid_name',
            )
        
        errors = {}
        
        # Validate year alignment
        if start_date.year != name_start_year:
            errors['start_date'] = _(
                f'Start date year ({start_date.year}) must match name start year ({name_start_year}). '
                f'Use a date like {name_start_year}-09-01'
            )
        
        if end_date.year != name_end_year:
            errors['end_date'] = _(
                f'End date year ({end_date.year}) must match name end year ({name_end_year}). '
                f'Use a date like {name_end_year}-08-31'
            )
        
        # Only check date order and duration if year alignment is correct
        if not errors:
            if start_date >= end_date:
                errors['end_date'] = _('End date must be after start date')
            else:
                # Check duration
                duration_days = (end_date - start_date).days
                
                if duration_days < AcademicYearValidator.MIN_DURATION_DAYS:
                    errors['end_date'] = _(
                        f'Academic year duration too short ({duration_days} days). '
                        f'Minimum {AcademicYearValidator.MIN_DURATION_DAYS} days (~10 months)'
                    )
                elif duration_days > AcademicYearValidator.MAX_DURATION_DAYS:
                    errors['end_date'] = _(
                        f'Academic year duration too long ({duration_days} days). '
                        f'Maximum {AcademicYearValidator.MAX_DURATION_DAYS} days (~14 months)'
                    )
        
        if errors:
            raise ValidationError(errors)
        
        return True
    
    @staticmethod
    def validate_all(name, start_date, end_date):
        """
        Comprehensive validation of all academic year fields.
        
        Args:
            name (str): Academic year name
            start_date (date): Start date
            end_date (date): End date
            
        Raises:
            ValidationError: If any validation fails
        """
        AcademicYearValidator.validate_name(name)
        AcademicYearValidator.validate_dates(name, start_date, end_date)