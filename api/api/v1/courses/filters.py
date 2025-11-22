"""
Courses App Filters
"""

from django_filters import rest_framework as filters
from apps.courses.models import Subject, Course, CoursePath, PathModule


class SubjectFilter(filters.FilterSet):
    """Filters for Subject."""
    
    level = filters.ChoiceFilter(choices=Subject.LEVEL_CHOICES)
    is_active = filters.BooleanFilter()
    
    class Meta:
        model = Subject
        fields = ['name', 'code', 'level', 'is_active']


class CourseFilter(filters.FilterSet):
    """Filters for Course."""
    
    subject = filters.NumberFilter(field_name='subject__id')
    level = filters.ChoiceFilter(
        choices=[('SCHOOL', 'School'), ('UNIV', 'University')]
    )
    is_active = filters.BooleanFilter()
    
    class Meta:
        model = Course
        fields = ['subject', 'level', 'is_active']


class CoursePathFilter(filters.FilterSet):
    """Filters for CoursePath."""
    
    course = filters.NumberFilter(field_name='course__id')
    scope = filters.ChoiceFilter(choices=CoursePath.SCOPE_CHOICES)
    is_published = filters.BooleanFilter()
    generation_status = filters.ChoiceFilter(
        choices=CoursePath.GENERATION_STATUS_CHOICES
    )
    
    class Meta:
        model = CoursePath
        fields = ['course', 'scope', 'is_published', 'generation_status']


class PathModuleFilter(filters.FilterSet):
    """Filters for PathModule."""
    
    path = filters.NumberFilter(field_name='path__id')
    category = filters.CharFilter(lookup_expr='icontains')
    is_published = filters.BooleanFilter()
    
    class Meta:
        model = PathModule
        fields = ['path', 'category', 'is_published']