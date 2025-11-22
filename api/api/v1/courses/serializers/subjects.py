"""
Subject Serializers
"""

from rest_framework import serializers
from apps.courses.models import Subject


class SubjectListSerializer(serializers.ModelSerializer):
    """List view for Subject (minimal fields)."""
    
    class Meta:
        model = Subject
        fields = [
            'id',
            'name',
            'code',
            'level',
            'is_active',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class SubjectDetailSerializer(serializers.ModelSerializer):
    """Detail view for Subject (all fields with tool configs)."""
    
    class Meta:
        model = Subject
        fields = [
            'id',
            'name',
            'code',
            'description',
            'level',
            # Tool availability
            'ppt_generator',
            'flashcard_creator',
            'quiz_generator',
            'lesson_plan_generator',
            'worksheet_generator',
            'mind_map_generator',
            'simulation',
            'practice_problems',
            'step_by_step_solver',
            # Teacher-only restrictions
            'ppt_generator_teacher_only',
            'flashcard_creator_teacher_only',
            'quiz_generator_teacher_only',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']