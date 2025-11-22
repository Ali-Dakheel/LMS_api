"""
Academics API Serializers - K-12 Focus

Exports all serializers for easy importing in views.
"""

# Structure
from .structure import (
    AcademicYearSerializer,
    TermListSerializer,
    TermDetailSerializer,
    TermWriteSerializer,
    ClassSectionListSerializer,
    ClassSectionDetailSerializer,
    ClassSectionWriteSerializer,
)

# Offerings
from .offerings import (
    OfferingTeacherSerializer,
    CourseOfferingListSerializer,
    CourseOfferingDetailSerializer,
    CourseOfferingWriteSerializer,
    ClassSessionSerializer,
    AttendanceSerializer,
)

# Enrollments
from .enrollments import (
    EnrollmentListSerializer,
    EnrollmentDetailSerializer,
    EnrollmentCreateSerializer,
    EnrollmentWaitlistSerializer,
    StudentEligibilitySerializer,
)

# Assignments
from .assignments import (
    TeacherTermSerializer,
    TeacherSubjectSerializer,
    StudentSectionSerializer,
    StudentSubjectSerializer,
)

__all__ = [
    # Structure
    'AcademicYearSerializer',
    'TermListSerializer',
    'TermDetailSerializer',
    'TermWriteSerializer',
    'ClassSectionListSerializer',
    'ClassSectionDetailSerializer',
    'ClassSectionWriteSerializer',

    # Offerings
    'OfferingTeacherSerializer',
    'CourseOfferingListSerializer',
    'CourseOfferingDetailSerializer',
    'CourseOfferingWriteSerializer',
    'ClassSessionSerializer',
    'AttendanceSerializer',

    # Enrollments
    'EnrollmentListSerializer',
    'EnrollmentDetailSerializer',
    'EnrollmentCreateSerializer',
    'EnrollmentWaitlistSerializer',
    'StudentEligibilitySerializer',

    # Assignments
    'TeacherTermSerializer',
    'TeacherSubjectSerializer',
    'StudentSectionSerializer',
    'StudentSubjectSerializer',
]