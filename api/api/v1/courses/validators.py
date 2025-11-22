"""
Courses App Custom Validators
"""

from rest_framework.exceptions import ValidationError
from django.core.exceptions import ValidationError as DjangoValidationError
from apps.courses.models import CoursePath


def validate_path_dates(data):
    """
    Validate path dates are within term dates (if offering scope).
    """
    if data.get('scope') != 'offering':
        return
    
    offering = data.get('offering')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    
    if not offering or not start_date or not end_date:
        return
    
    term = offering.term
    
    if start_date < term.start_date:
        raise ValidationError(
            {'start_date': 'Start date must be after term start date'}
        )
    
    if end_date > term.end_date:
        raise ValidationError(
            {'end_date': 'End date must be before term end date'}
        )


def validate_scope_consistency(data):
    """
    Validate scope-specific fields are present.
    """
    scope = data.get('scope')
    
    if scope == 'teacher' and not data.get('teacher'):
        raise ValidationError({'teacher': 'Teacher required for teacher scope'})
    
    if scope == 'student' and not data.get('student'):
        raise ValidationError({'student': 'Student required for student scope'})
    
    if scope == 'offering' and not data.get('offering'):
        raise ValidationError({'offering': 'Offering required for offering scope'})