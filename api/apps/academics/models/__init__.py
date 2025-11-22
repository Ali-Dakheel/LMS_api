"""
Academics App Models - K-12 Focus

Exports all models for easy importing.

Organization:
- base: Foundation models (AcademicYear)
- structure: Organizational units (Term, ClassSection)
- offerings: Course delivery (CourseOffering, OfferingTeacher, ClassSession, Attendance)
- enrollments: Student enrollment (Enrollment, EnrollmentWaitlist, StudentEligibility)
- assignments: Relationship assignments (Teacher, Student)
"""

# Base models
from .base import (
    AcademicYear,
)

# Structure models
from .structure import (
    Term,
    ClassSection,
)

# Offering models
from .offerings import (
    CourseOffering,
    OfferingTeacher,
    ClassSession,
    Attendance,
)

# Enrollment models
from .enrollments import (
    Enrollment,
    EnrollmentWaitlist,
    StudentEligibility,
)

# Assignment models
from .assignments import (
    TeacherSubject,
    TeacherTerm,
    StudentSection,
    StudentSubject,
)

# Managers (for reference)
from .managers import (
    CourseOfferingManager,
    EnrollmentManager,
    OfferingTeacherManager,
)

__all__ = [
    # Base
    'AcademicYear',

    # Structure
    'Term',
    'ClassSection',

    # Offerings
    'CourseOffering',
    'OfferingTeacher',
    'ClassSession',
    'Attendance',

    # Enrollments
    'Enrollment',
    'EnrollmentWaitlist',
    'StudentEligibility',

    # Assignments
    'TeacherSubject',
    'TeacherTerm',
    'StudentSection',
    'StudentSubject',

    # Managers
    'CourseOfferingManager',
    'EnrollmentManager',
    'OfferingTeacherManager',
]