"""
Enrollment Serializers

Serializers for Enrollment, EnrollmentWaitlist, StudentEligibility
"""

from rest_framework import serializers
from apps.academics.models import (
    Enrollment,
    EnrollmentWaitlist,
    StudentEligibility,
)
from .offerings import CourseOfferingListSerializer


class EnrollmentListSerializer(serializers.ModelSerializer):
    """List serializer for Enrollment (minimal fields)."""
    
    student_name = serializers.CharField(source='student.name', read_only=True)
    student_email = serializers.CharField(source='student.email', read_only=True)
    offering_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Enrollment
        fields = [
            'id',
            'student',
            'student_name',
            'student_email',
            'offering',
            'offering_name',
            'status',
            'enrolled_at',
        ]
        read_only_fields = ['id', 'enrolled_at']
    
    def get_offering_name(self, obj):
        return f"{obj.offering.course.title} - {obj.offering.class_section.name}"


class EnrollmentDetailSerializer(serializers.ModelSerializer):
    """Detail serializer for Enrollment (all fields)."""
    
    offering = CourseOfferingListSerializer(read_only=True)
    student_name = serializers.CharField(source='student.name', read_only=True)
    
    class Meta:
        model = Enrollment
        fields = [
            'id',
            'student',
            'student_name',
            'offering',
            'status',
            'enrolled_at',
            'dropped_at',
            'completed_at',
            'final_grade',
            'created_at',
        ]
        read_only_fields = ['id', 'enrolled_at', 'dropped_at', 'completed_at', 'created_at']


class EnrollmentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating enrollments."""
    
    class Meta:
        model = Enrollment
        fields = ['student', 'offering']
    
    def validate(self, data):
        """Validate enrollment creation."""
        student = data['student']
        offering = data['offering']
        
        # Check if already enrolled
        if Enrollment.objects.filter(student=student, offering=offering).exists():
            raise serializers.ValidationError("Student is already enrolled in this offering")
        
        # Check capacity
        if offering.is_full():
            raise serializers.ValidationError("This offering is at full capacity")
        
        # Check eligibility
        from apps.academics.models import StudentEligibility
        eligibility = StudentEligibility.objects.filter(
            student=student,
            course=offering.course,
            status='approved'
        ).first()
        
        if not eligibility:
            raise serializers.ValidationError("Student is not eligible for this course")
        
        return data


class EnrollmentWaitlistSerializer(serializers.ModelSerializer):
    """Serializer for EnrollmentWaitlist."""
    
    student_name = serializers.CharField(source='student.name', read_only=True)
    offering_name = serializers.SerializerMethodField()
    
    class Meta:
        model = EnrollmentWaitlist
        fields = [
            'id',
            'student',
            'student_name',
            'offering',
            'offering_name',
            'position',
            'added_at',
            'notified_at',
        ]
        read_only_fields = ['id', 'position', 'added_at', 'notified_at']
    
    def get_offering_name(self, obj):
        return f"{obj.offering.course.title} - {obj.offering.class_section.name}"


class StudentEligibilitySerializer(serializers.ModelSerializer):
    """Serializer for StudentEligibility (K-12 Focus)."""

    student_name = serializers.CharField(source='student.name', read_only=True)
    course_title = serializers.CharField(source='course.title', read_only=True)

    class Meta:
        model = StudentEligibility
        fields = [
            'id',
            'student',
            'student_name',
            'course',
            'course_title',
            'status',
            'reason',
            'overridden_by',
            'overridden_at',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'overridden_at', 'created_at', 'updated_at']