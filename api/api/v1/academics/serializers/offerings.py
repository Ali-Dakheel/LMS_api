"""
Course Offering Serializers

Serializers for CourseOffering, OfferingTeacher, ClassSession, Attendance
"""

from rest_framework import serializers
from apps.academics.models import (
    CourseOffering,
    OfferingTeacher,
    ClassSession,
    Attendance,
    ClassSection,
    Term,
)
from apps.courses.models import Course
from .structure import TermListSerializer, ClassSectionListSerializer


class OfferingTeacherSerializer(serializers.ModelSerializer):
    """Serializer for OfferingTeacher."""
    
    teacher_name = serializers.CharField(source='teacher.name', read_only=True)
    teacher_email = serializers.CharField(source='teacher.email', read_only=True)
    
    class Meta:
        model = OfferingTeacher
        fields = [
            'id',
            'teacher',
            'teacher_name',
            'teacher_email',
            'is_primary',
            'assigned_at',
        ]
        read_only_fields = ['id', 'teacher_name', 'teacher_email', 'assigned_at']


class CourseOfferingListSerializer(serializers.ModelSerializer):
    """List serializer for CourseOffering (minimal fields)."""
    
    course_title = serializers.CharField(source='course.title', read_only=True)
    course_code = serializers.CharField(source='course.code', read_only=True)
    term_name = serializers.CharField(source='term.name', read_only=True)
    section_name = serializers.CharField(source='class_section.name', read_only=True)
    
    class Meta:
        model = CourseOffering
        fields = [
            'id',
            'course',
            'course_title',
            'course_code',
            'term',
            'term_name',
            'class_section',
            'section_name',
            'slug',
            'is_active',
        ]


class CourseOfferingDetailSerializer(serializers.ModelSerializer):
    """Detail serializer for CourseOffering (all fields)."""

    term = TermListSerializer(read_only=True)
    class_section = ClassSectionListSerializer(read_only=True)
    teachers = OfferingTeacherSerializer(many=True, read_only=True)
    course_title = serializers.CharField(source='course.title', read_only=True)
    enrollment_count = serializers.IntegerField(read_only=True)
    available_seats = serializers.IntegerField(read_only=True)

    class Meta:
        model = CourseOffering
        fields = [
            'id',
            'course',
            'course_title',
            'term',
            'class_section',
            'slug',
            'capacity',
            'auto_enroll',
            'generation_status',
            'is_active',
            'teachers',
            'enrollment_count',
            'available_seats',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'slug', 'enrollment_count', 'available_seats', 'created_at', 'updated_at']

class CourseOfferingWriteSerializer(serializers.ModelSerializer):
    """
    Write serializer for CourseOffering (create/update).
    
    Accepts FK IDs for course, term, class_section.
    Validates relationships and uniqueness.
    """

    class Meta:
        model = CourseOffering
        fields = [
            'id',
            'course',
            'term',
            'class_section',
            'capacity',
            'auto_enroll',
            'generation_status',
            'is_active',
        ]
        read_only_fields = ['id']
    
    def validate_course(self, value):
        """Validate course exists and is active."""
        if not Course.objects.filter(id=value.id, is_active=True).exists():
            raise serializers.ValidationError(
                f'Course with ID {value.id} does not exist or is inactive.'
            )
        return value
    
    def validate_term(self, value):
        """Validate term exists."""
        if not Term.objects.filter(id=value.id).exists():
            raise serializers.ValidationError(
                f'Term with ID {value.id} does not exist.'
            )
        return value
    
    def validate_class_section(self, value):
        """Validate class section exists."""
        if not ClassSection.objects.filter(id=value.id).exists():
            raise serializers.ValidationError(
                f'Class section with ID {value.id} does not exist.'
            )
        return value
    
    def validate_capacity(self, value):
        """Validate capacity if provided."""
        if value is not None and value < 1:
            raise serializers.ValidationError('Capacity must be at least 1.')
        return value
    
    def validate(self, data):
        """Validate uniqueness and relationships."""
        course = data.get('course')
        term = data.get('term')
        class_section = data.get('class_section')
        instance = self.instance
        
        if course and term and class_section:
            # Check unique_together constraint
            queryset = CourseOffering.objects.filter(
                course=course,
                term=term,
                class_section=class_section
            )
            
            # For updates, exclude current instance
            if instance:
                queryset = queryset.exclude(pk=instance.pk)
            
            if queryset.exists():
                raise serializers.ValidationError({
                    'non_field_errors': [
                        f'Course offering already exists for '
                        f'{course.title} in {term.name} for {class_section.name}.'
                    ]
                })
        
        return data

class ClassSessionSerializer(serializers.ModelSerializer):
    """Serializer for ClassSession."""
    
    offering_name = serializers.SerializerMethodField()
    
    class Meta:
        model = ClassSession
        fields = [
            'id',
            'offering',
            'offering_name',
            'session_date',
            'start_time',
            'end_time',
            'topic',
            'notes',
            'is_cancelled',
            'cancellation_reason',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_offering_name(self, obj):
        return f"{obj.offering.course.title} - {obj.offering.class_section.name}"


class AttendanceSerializer(serializers.ModelSerializer):
    """Serializer for Attendance."""

    student_name = serializers.CharField(source='student.name', read_only=True)
    student_email = serializers.CharField(source='student.email', read_only=True)
    marked_by_name = serializers.CharField(source='marked_by.name', read_only=True, allow_null=True)
    session_date = serializers.DateField(source='class_session.session_date', read_only=True)
    offering_name = serializers.SerializerMethodField()

    class Meta:
        model = Attendance
        fields = [
            'id',
            'class_session',
            'student',
            'student_name',
            'student_email',
            'status',
            'notes',
            'marked_by',
            'marked_by_name',
            'session_date',
            'offering_name',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'student_name', 'student_email', 'marked_by_name', 'session_date', 'offering_name', 'created_at', 'updated_at']

    def get_offering_name(self, obj):
        """Get offering name from session."""
        return f"{obj.class_session.offering.course.title} - {obj.class_session.offering.class_section.name}"