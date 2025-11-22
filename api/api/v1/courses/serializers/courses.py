"""
Course Serializers
"""

from rest_framework import serializers
from apps.courses.models import Course
from .subjects import SubjectDetailSerializer


class CourseListSerializer(serializers.ModelSerializer):
    """List view for Course (minimal fields)."""
    
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    subject_code = serializers.CharField(source='subject.code', read_only=True)
    
    class Meta:
        model = Course
        fields = [
            'id',
            'title',
            'code',
            'subject',
            'subject_name',
            'subject_code',
            'level',
            'slug',
            'is_active',
            'created_at',
        ]
        read_only_fields = ['id', 'slug', 'created_at']


class CourseCreateUpdateSerializer(serializers.ModelSerializer):
    """Create/Update serializer for Course (writable fields)."""
    
    class Meta:
        model = Course
        fields = [
            'id',
            'title',
            'code',
            'description',
            'subject',
            'level',
            'credit_hours',
            'outcomes',
            'syllabus_file',
            'is_active',
        ]
        read_only_fields = ['id']


class CourseDetailSerializer(serializers.ModelSerializer):
    """Detail view for Course (all fields with nested subject)."""
    
    subject = SubjectDetailSerializer(read_only=True)
    
    class Meta:
        model = Course
        fields = [
            'id',
            'title',
            'code',
            'slug',
            'description',
            'subject',
            'level',
            'credit_hours',
            'outcomes',
            'syllabus_file',
            'syllabus_analysis_status',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']
