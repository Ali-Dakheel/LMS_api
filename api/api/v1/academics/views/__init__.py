"""
Academics API Views - K-12 Focus

Exports all view classes for URL routing.
"""

# Structure
from .structure import (
    AcademicYearViewSet,
    TermViewSet,
    ClassSectionViewSet,
)

# Offerings
from .offerings import (
    CourseOfferingViewSet,
    OfferingTeacherViewSet,
    ClassSessionViewSet,
    AttendanceViewSet,
)

# Enrollments
from .enrollments import (
    EnrollmentViewSet,
    EnrollmentWaitlistViewSet,
    StudentEligibilityViewSet,
)

# Assignments
from .assignments import (
    TeacherTermViewSet,
    TeacherSubjectViewSet,
    StudentSectionViewSet,
    StudentSubjectViewSet,
)

__all__ = [
    # Structure
    'AcademicYearViewSet',
    'TermViewSet',
    'ClassSectionViewSet',

    # Offerings
    'CourseOfferingViewSet',
    'OfferingTeacherViewSet',
    'ClassSessionViewSet',
    'AttendanceViewSet',

    # Enrollments
    'EnrollmentViewSet',
    'EnrollmentWaitlistViewSet',
    'StudentEligibilityViewSet',

    # Assignments
    'TeacherTermViewSet',
    'TeacherSubjectViewSet',
    'StudentSectionViewSet',
    'StudentSubjectViewSet',
]