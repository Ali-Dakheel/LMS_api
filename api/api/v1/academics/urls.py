"""
Academics API URLs - K-12 Focus

URL routing for all academic endpoints.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    # Structure
    AcademicYearViewSet,
    TermViewSet,
    ClassSectionViewSet,
    # Offerings
    CourseOfferingViewSet,
    ClassSessionViewSet,
    AttendanceViewSet,
    OfferingTeacherViewSet,
    # Enrollments
    EnrollmentViewSet,
    EnrollmentWaitlistViewSet,
    StudentEligibilityViewSet,
    # Assignments
    TeacherTermViewSet,
    TeacherSubjectViewSet,
    StudentSectionViewSet,
    StudentSubjectViewSet,
)

# Create router
router = DefaultRouter()

# ============================================================================
# STRUCTURE ENDPOINTS - K-12
# ============================================================================
router.register(r'academic-years', AcademicYearViewSet, basename='academic-year')
router.register(r'terms', TermViewSet, basename='term')
router.register(r'sections', ClassSectionViewSet, basename='section')

# ============================================================================
# OFFERINGS ENDPOINTS
# ============================================================================
router.register(r'offerings', CourseOfferingViewSet, basename='offering')
router.register(r'offering-teachers', OfferingTeacherViewSet, basename='offering-teacher')
router.register(r'sessions', ClassSessionViewSet, basename='session')
router.register(r'attendance', AttendanceViewSet, basename='attendance')

# ============================================================================
# ENROLLMENTS ENDPOINTS
# ============================================================================
router.register(r'enrollments', EnrollmentViewSet, basename='enrollment')
router.register(r'waitlist', EnrollmentWaitlistViewSet, basename='waitlist')
router.register(r'eligibility', StudentEligibilityViewSet, basename='eligibility')

# ============================================================================
# ASSIGNMENT ENDPOINTS - K-12
# ============================================================================
router.register(r'teacher-terms', TeacherTermViewSet, basename='teacher-term')
router.register(r'teacher-subjects', TeacherSubjectViewSet, basename='teacher-subject')
router.register(r'student-sections', StudentSectionViewSet, basename='student-section')
router.register(r'student-subjects', StudentSubjectViewSet, basename='student-subject')

# URL patterns
urlpatterns = [
    path('', include(router.urls)),
]
