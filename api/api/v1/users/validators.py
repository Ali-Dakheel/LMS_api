"""
Custom validators for user-related fields.

Provides reusable validation logic for:
- Enrollment number format
- Profile image size and type
- Email domain restrictions (if needed)
"""

from typing import List, Optional
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.core.files.uploadedfile import UploadedFile
import re


def validate_enrollment_number_format(value: str) -> None:
    """
    Validate enrollment number format for students.

    Expected format: YEAR-DEPT-NUMBER (e.g., 2024-CS-001, 2023-MATH-042)

    Args:
        value: Enrollment number string

    Raises:
        ValidationError: If format is invalid

    Examples:
        Valid: "2024-CS-001", "2023-MATH-042", "2025-BIO-1234"
        Invalid: "2024CS001", "CS-001", "2024-001"
    """
    pattern = r'^\d{4}-[A-Z]{2,4}-\d{3,4}$'
    if not re.match(pattern, value):
        raise ValidationError(
            f"Invalid enrollment number format. Expected: YEAR-DEPT-NUMBER (e.g., 2024-CS-001)",
            code='invalid_enrollment_format'
        )


def validate_profile_image_size(image: UploadedFile) -> None:
    """
    Validate profile image file size.

    Args:
        image: UploadedFile object

    Raises:
        ValidationError: If image exceeds size limit
    """
    max_size = 5 * 1024 * 1024  # 5MB in bytes
    if image.size > max_size:
        raise ValidationError(
            f"Image size cannot exceed 5MB. Current size: {image.size / (1024*1024):.2f}MB",
            code='file_too_large'
        )


def validate_profile_image_extension(filename: str) -> None:
    """
    Validate profile image file extension.

    Args:
        filename: Name of the uploaded file

    Raises:
        ValidationError: If extension is not allowed
    """
    allowed_extensions = ['jpg', 'jpeg', 'png', 'gif']
    ext = filename.split('.')[-1].lower() if '.' in filename else ''

    if ext not in allowed_extensions:
        raise ValidationError(
            f"Only {', '.join(allowed_extensions)} files are allowed",
            code='invalid_file_type'
        )


def validate_institution_email_domain(email: str, allowed_domains: Optional[List[str]] = None) -> None:
    """
    Validate email belongs to allowed institutional domains.

    Optional validator for restricting user registration to specific domains.

    Args:
        email: Email address to validate
        allowed_domains: List of allowed domain names (e.g., ['university.edu', 'school.org'])

    Raises:
        ValidationError: If email domain is not allowed

    Example:
        validate_institution_email_domain('user@university.edu', ['university.edu'])
    """
    if not allowed_domains:
        return  # No restriction

    domain = email.split('@')[-1].lower() if '@' in email else ''

    if domain not in allowed_domains:
        raise ValidationError(
            f"Email must be from one of these domains: {', '.join(allowed_domains)}",
            code='invalid_email_domain'
        )


# Regex validator for phone numbers (international format)
phone_number_validator = RegexValidator(
    regex=r'^\+?1?\d{9,15}$',
    message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.",
    code='invalid_phone_number'
)


# Regex validator for designation/title
designation_validator = RegexValidator(
    regex=r'^[a-zA-Z\s\-\.]+$',
    message="Designation can only contain letters, spaces, hyphens, and periods.",
    code='invalid_designation'
)
