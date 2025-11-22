"""
Academics API Filters - K-12 Focus

Django-filter classes for querying academic resources.
"""

from django_filters import rest_framework as filters
from django.utils import timezone
from apps.academics.models import (
    AcademicYear,
    Term,
    CourseOffering,
    Enrollment,
    ClassSection,
)


class AcademicYearFilter(filters.FilterSet):
    """Filter for AcademicYear."""

    is_current = filters.BooleanFilter(field_name='is_current')
    year = filters.NumberFilter(field_name='start_date__year')

    class Meta:
        model = AcademicYear
        fields = ['is_current', 'year']


class TermFilter(filters.FilterSet):
    """Filter for Term (Grade Levels) - K-12 Focus."""

    academic_year = filters.NumberFilter(field_name='academic_year__id')
    is_current = filters.BooleanFilter(method='filter_is_current')
    number = filters.NumberFilter(field_name='number')

    class Meta:
        model = Term
        fields = ['academic_year', 'number']

    def filter_is_current(self, queryset, name, value):
        """Filter terms that are currently active."""
        now = timezone.now().date()
        if value:
            return queryset.filter(start_date__lte=now, end_date__gte=now)
        return queryset


class ClassSectionFilter(filters.FilterSet):
    """Filter for ClassSection - K-12 Focus."""

    term = filters.NumberFilter(field_name='term__id')
    section = filters.CharFilter(field_name='section', lookup_expr='iexact')
    homeroom_teacher = filters.NumberFilter(field_name='homeroom_teacher__id')
    is_active = filters.BooleanFilter(field_name='is_active')

    class Meta:
        model = ClassSection
        fields = ['term', 'section', 'homeroom_teacher', 'is_active']


class CourseOfferingFilter(filters.FilterSet):
    """Filter for CourseOffering."""
    
    course = filters.NumberFilter(field_name='course__id')
    term = filters.NumberFilter(field_name='term__id')
    class_section = filters.NumberFilter(field_name='class_section__id')
    teacher = filters.NumberFilter(field_name='teachers__teacher__id')
    is_active = filters.BooleanFilter(field_name='is_active')
    
    class Meta:
        model = CourseOffering
        fields = ['course', 'term', 'class_section', 'teacher', 'is_active']


class EnrollmentFilter(filters.FilterSet):
    """Filter for Enrollment."""
    
    student = filters.NumberFilter(field_name='student__id')
    offering = filters.NumberFilter(field_name='offering__id')
    status = filters.ChoiceFilter(choices=[
        ('active', 'Active'),
        ('dropped', 'Dropped'),
        ('completed', 'Completed'),
        ('withdrawn', 'Withdrawn'),
    ])
    
    class Meta:
        model = Enrollment
        fields = ['student', 'offering', 'status']