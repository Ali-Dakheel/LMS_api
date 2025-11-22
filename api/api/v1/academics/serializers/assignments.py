"""
Academic Assignment Serializers - K-12 Focus

Serializers for TeacherTerm, TeacherSubject, StudentSection, StudentSubject
"""

from rest_framework import serializers
from apps.academics.models import (
    TeacherTerm,
    TeacherSubject,
    StudentSection,
    StudentSubject,
)


class TeacherTermSerializer(serializers.ModelSerializer):
    """Serializer for TeacherTerm (Grade assignments) - K-12 Focus."""

    teacher_name = serializers.CharField(source='teacher.name', read_only=True)
    term_name = serializers.CharField(source='term.name', read_only=True)

    class Meta:
        model = TeacherTerm
        fields = [
            'id',
            'teacher',
            'teacher_name',
            'term',
            'term_name',
            'assigned_at',
            'is_active',
        ]
        read_only_fields = ['id', 'assigned_at']


class TeacherSubjectSerializer(serializers.ModelSerializer):
    """Serializer for TeacherSubject - K-12 Focus."""

    teacher_name = serializers.CharField(source='teacher.name', read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)

    class Meta:
        model = TeacherSubject
        fields = [
            'id',
            'teacher',
            'teacher_name',
            'subject',
            'subject_name',
            'assigned_at',
        ]
        read_only_fields = ['id', 'assigned_at']


class StudentSectionSerializer(serializers.ModelSerializer):
    """Serializer for StudentSection (Homeroom assignments) - K-12 Focus."""

    student_name = serializers.CharField(source='student.name', read_only=True)
    section_name = serializers.CharField(source='class_section.name', read_only=True)

    class Meta:
        model = StudentSection
        fields = [
            'id',
            'student',
            'student_name',
            'class_section',
            'section_name',
            'enrolled_at',
        ]
        read_only_fields = ['id', 'enrolled_at']


class StudentSubjectSerializer(serializers.ModelSerializer):
    """Serializer for StudentSubject - K-12 Focus."""

    student_name = serializers.CharField(source='student.name', read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    term_name = serializers.CharField(source='term.name', read_only=True, allow_null=True)

    class Meta:
        model = StudentSubject
        fields = [
            'id',
            'student',
            'student_name',
            'subject',
            'subject_name',
            'term',
            'term_name',
            'assigned_at',
            'is_active',
        ]
        read_only_fields = ['id', 'assigned_at']
