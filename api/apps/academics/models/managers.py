"""
Academics App Custom Managers - K-12 Focus

All QuerySet and Manager classes for academics models.
Centralized for easy maintenance and reusability.
"""

from django.db import models
from django.db.models import Prefetch, Q, Count
from django.apps import apps


# ============================================================================
# COURSE OFFERING MANAGERS
# ============================================================================

class CourseOfferingQuerySet(models.QuerySet):
    """Custom QuerySet for CourseOffering with optimized queries for K-12."""

    def with_teachers(self):
        """Prefetch teachers with their user info."""
        return self.prefetch_related(
            'teachers__teacher'
        )

    def with_enrollments(self):
        """Prefetch enrolled students."""
        Enrollment = apps.get_model('academics', 'Enrollment')
        return self.prefetch_related(
            Prefetch(
                'enrollments',
                queryset=Enrollment.objects
                    .filter(status='active')
                    .select_related('student')
            )
        )

    def with_all_relations(self):
        """Full eager loading for detail views (K-12)."""
        return self.select_related(
            'course',
            'course__subject',
            'term',
            'term__academic_year',
            'class_section',
            'class_section__homeroom_teacher',
        ).with_teachers().with_enrollments()

    def for_term(self, term):
        """Filter by term (grade level)."""
        return self.filter(term=term)

    def for_grade(self, grade_number):
        """Filter by grade number (1-12)."""
        return self.filter(term__number=grade_number)

    def for_course(self, course):
        """Filter by course."""
        return self.filter(course=course)

    def for_section(self, section):
        """Filter by class section."""
        return self.filter(class_section=section)

    def for_teacher(self, teacher):
        """Filter offerings taught by teacher."""
        return self.filter(teachers__teacher=teacher).distinct()

    def active(self):
        """Filter active offerings only."""
        return self.filter(is_active=True)

    def with_enrollment_stats(self):
        """Add enrollment count and capacity info."""
        return self.annotate(
            enrolled_count=Count(
                'enrollments',
                filter=Q(enrollments__status__in=['active', 'pending'])
            )
        )

    def search(self, query):
        """Full-text search in course title and section name."""
        return self.filter(
            Q(course__title__icontains=query) |
            Q(class_section__name__icontains=query)
        )


class CourseOfferingManager(models.Manager):
    """Manager for CourseOffering with QuerySet methods."""
    
    def get_queryset(self):
        return CourseOfferingQuerySet(self.model, using=self._db)
    
    def with_all_relations(self):
        return self.get_queryset().with_all_relations()
    
    def active(self):
        return self.get_queryset().active()
    
    def for_teacher(self, teacher):
        return self.get_queryset().for_teacher(teacher)


# ============================================================================
# ENROLLMENT MANAGERS
# ============================================================================

class EnrollmentQuerySet(models.QuerySet):
    """Custom QuerySet for Enrollment with optimizations."""
    
    def with_student_info(self):
        """Prefetch student details."""
        return self.select_related('student', 'student__student_info')
    
    def with_offering_info(self):
        """Prefetch offering and course details."""
        return self.select_related(
            'offering',
            'offering__course',
            'offering__course__subject',
            'offering__term',
            'offering__class_section',
        )
    
    def with_all_relations(self):
        """Full eager loading."""
        return self.with_student_info().with_offering_info()
    
    def active_only(self):
        """Filter active enrollments."""
        return self.filter(status='active')
    
    def for_student(self, student):
        """Filter by student."""
        return self.filter(student=student)
    
    def for_offering(self, offering):
        """Filter by offering."""
        return self.filter(offering=offering)
    
    def for_term(self, term):
        """Filter by term."""
        return self.filter(offering__term=term)
    
    def by_status(self, *statuses):
        """Filter by one or more statuses."""
        return self.filter(status__in=statuses)


class EnrollmentManager(models.Manager):
    """Manager for Enrollment with QuerySet."""
    
    def get_queryset(self):
        return EnrollmentQuerySet(self.model, using=self._db)
    
    def with_all_relations(self):
        return self.get_queryset().with_all_relations()
    
    def active_only(self):
        return self.get_queryset().active_only()
    
    def for_student(self, student):
        return self.get_queryset().for_student(student)


# ============================================================================
# OFFERING TEACHER MANAGER
# ============================================================================

class OfferingTeacherManager(models.Manager):
    """Manager for OfferingTeacher (K-12)."""

    def get_queryset(self):
        return super().get_queryset().select_related(
            'offering__course',
            'offering__class_section',
            'teacher'
        )

    def primary_only(self):
        """Get only primary teachers."""
        return self.filter(is_primary=True)

    def for_teacher(self, teacher):
        """Get all offerings taught by teacher."""
        return self.filter(teacher=teacher)