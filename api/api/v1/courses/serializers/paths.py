"""
CoursePath Serializers
"""

from rest_framework import serializers
from apps.courses.models import CoursePath
from .courses import CourseListSerializer


class CoursePathListSerializer(serializers.ModelSerializer):
    """List view for CoursePath (minimal fields)."""
    
    course_title = serializers.CharField(source='course.title', read_only=True)
    scope_display = serializers.CharField(source='get_scope_display', read_only=True)
    
    class Meta:
        model = CoursePath
        fields = [
            'id',
            'label',
            'slug',
            'course',
            'course_title',
            'scope',
            'scope_display',
            'is_published',
            'generation_status',
            'created_at',
        ]
        read_only_fields = ['id', 'slug', 'created_at']


class CoursePathCreateUpdateSerializer(serializers.ModelSerializer):
    """Create/Update serializer for CoursePath (writable fields)."""
    
    class Meta:
        model = CoursePath
        fields = [
            'id',
            'label',
            'description',
            'objectives',
            'outcomes',
            'course',
            'scope',
            'teacher',
            'student',
            'offering',
            'start_date',
            'end_date',
            'source_kind',
            'source_book',
            'source_toc_item',
            'generation_status',
            'is_published',
            'order',
        ]
        read_only_fields = ['id']


class CoursePathDetailSerializer(serializers.ModelSerializer):
    """Detail view for CoursePath (all fields)."""
    
    course = CourseListSerializer(read_only=True)
    scope_display = serializers.CharField(source='get_scope_display', read_only=True)
    source_kind_display = serializers.CharField(source='get_source_kind_display', read_only=True)
    
    class Meta:
        model = CoursePath
        fields = [
            'id',
            'label',
            'slug',
            'description',
            'objectives',
            'outcomes',
            'course',
            'scope',
            'scope_display',
            'teacher',
            'student',
            'offering',
            'start_date',
            'end_date',
            'source_kind',
            'source_kind_display',
            'source_book',
            'source_toc_item',
            'generation_status',
            'is_published',
            'published_at',
            'order',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id', 'slug', 'published_at', 'created_at', 'updated_at'
        ]
