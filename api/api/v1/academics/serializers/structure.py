"""
Academic Structure Serializers - K-12 Focus

Serializers for AcademicYear, Term, ClassSection
"""

from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from apps.academics.models import (
    AcademicYear,
    Term,
    ClassSection,
)
from apps.academics.validators import AcademicYearValidator
from django.core.exceptions import ValidationError as DjangoValidationError


class AcademicYearSerializer(serializers.ModelSerializer):
    """
    Serializer for AcademicYear with comprehensive validation.

    Features:
    - Field-level validation via validators
    - Object-level validation for relationships
    - Read-only computed fields (duration_days, duration_months, is_active)
    - Helpful error messages
    """

    duration_days = serializers.IntegerField(read_only=True)
    duration_months = serializers.FloatField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = AcademicYear
        fields = [
            'id',
            'name',
            'start_date',
            'end_date',
            'duration_days',
            'duration_months',
            'is_active',
            'is_current',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'duration_days', 'duration_months', 'is_active']

    def validate_name(self, value):
        """
        Validate name format and year values.

        Delegates to AcademicYearValidator.validate_name()
        Converts ValidationError to serializers.ValidationError for DRF
        """
        try:
            AcademicYearValidator.validate_name(value)
        except DjangoValidationError as e:
            if hasattr(e, 'message_dict'):
                raise serializers.ValidationError(e.message_dict)
            elif hasattr(e, 'message'):
                raise serializers.ValidationError(e.message)
            else:
                raise serializers.ValidationError(str(e))
        return value

    def validate(self, data):
        """
        Validate relationships between name, start_date, and end_date.

        Delegates to AcademicYearValidator.validate_dates()
        Handles both create and update operations
        """
        name = data.get('name', self.instance.name if self.instance else None)
        start_date = data.get('start_date', self.instance.start_date if self.instance else None)
        end_date = data.get('end_date', self.instance.end_date if self.instance else None)

        if name and start_date and end_date:
            try:
                AcademicYearValidator.validate_dates(name, start_date, end_date)
            except DjangoValidationError as e:
                if hasattr(e, 'message_dict'):
                    raise serializers.ValidationError(e.message_dict)
                else:
                    raise serializers.ValidationError(str(e))

        return data


class TermListSerializer(serializers.ModelSerializer):
    """
    List serializer for Term (Grade Levels) - K-12 Focus.

    Minimal fields for list views.
    """

    academic_year_name = serializers.CharField(
        source='academic_year.name',
        read_only=True,
        help_text="Academic year name"
    )

    class Meta:
        model = Term
        fields = [
            'id',
            'name',
            'number',
            'academic_year',
            'academic_year_name',
            'start_date',
            'end_date',
            'is_current',
        ]
        read_only_fields = ['id']


class TermDetailSerializer(serializers.ModelSerializer):
    """
    Detail serializer for Term (Grade Levels) - K-12 Focus.

    Includes all fields and nested academic year.
    """

    academic_year = AcademicYearSerializer(read_only=True)

    class Meta:
        model = Term
        fields = [
            'id',
            'academic_year',
            'name',
            'number',
            'start_date',
            'end_date',
            'is_current',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class TermWriteSerializer(serializers.ModelSerializer):
    """
    Write serializer for Term creation/update - K-12 Focus.

    For creating/updating grade levels (1-12).
    """

    class Meta:
        model = Term
        fields = [
            'id',
            'academic_year',
            'number',
            'name',
            'start_date',
            'end_date',
            'is_current',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ClassSectionListSerializer(serializers.ModelSerializer):
    """List serializer for ClassSection (minimal fields, read-only)."""

    term_name = serializers.CharField(source='term.name', read_only=True)
    homeroom_teacher_name = serializers.CharField(
        source='homeroom_teacher.name',
        read_only=True,
        allow_null=True
    )

    class Meta:
        model = ClassSection
        fields = [
            'id',
            'name',
            'term',
            'term_name',
            'section',
            'homeroom_teacher',
            'homeroom_teacher_name',
            'capacity',
            'is_active',
        ]
        read_only_fields = [
            'id',
            'term',
            'term_name',
            'homeroom_teacher',
            'homeroom_teacher_name',
        ]


class ClassSectionDetailSerializer(serializers.ModelSerializer):
    """
    Detail serializer for ClassSection (all fields, read-only).
    
    Includes nested Term and Teacher data.
    """

    term = serializers.SerializerMethodField()
    homeroom_teacher_name = serializers.CharField(
        source='homeroom_teacher.name',
        read_only=True,
        allow_null=True
    )

    class Meta:
        model = ClassSection
        fields = [
            'id',
            'term',
            'name',
            'section',
            'capacity',
            'homeroom_teacher',
            'homeroom_teacher_name',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'term',
            'homeroom_teacher_name',
            'created_at',
            'updated_at'
        ]
    
    def get_term(self, obj):
        """Return nested Term data (not just ID)."""
        return TermListSerializer(obj.term).data


class ClassSectionWriteSerializer(serializers.ModelSerializer):
    """
    Write serializer for ClassSection (create/update).
    
    Accepts FK IDs for term and homeroom_teacher.
    Validates that term exists.
    """

    class Meta:
        model = ClassSection
        fields = [
            'id',
            'term',
            'name',
            'section',
            'capacity',
            'homeroom_teacher',
            'is_active',
        ]
        read_only_fields = ['id']
    
    def validate_term(self, value):
        """Validate term exists."""
        if not Term.objects.filter(id=value.id).exists():
            raise serializers.ValidationError(
                f'Term with ID {value.id} does not exist.'
            )
        return value
    
    def validate_homeroom_teacher(self, value):
        """Validate homeroom teacher is actually a teacher."""
        if value and value.role != 'teacher':
            raise serializers.ValidationError(
                'Homeroom teacher must have teacher role.'
            )
        return value
    
    def validate_capacity(self, value):
        """Validate capacity is within reasonable range."""
        if value < 1:
            raise serializers.ValidationError('Capacity must be at least 1.')
        if value > 50:
            raise serializers.ValidationError('Capacity cannot exceed 50 students.')
        return value
    
    def validate(self, data):
        """Validate section uniqueness for K-12."""
        term = data.get('term')
        section = data.get('section')
        instance = self.instance
        
        if term and section:
            # Check if section already exists for this term
            queryset = ClassSection.objects.filter(term=term, section=section)
            
            # For updates, exclude the current instance
            if instance:
                queryset = queryset.exclude(pk=instance.pk)
            
            if queryset.exists():
                raise serializers.ValidationError({
                    'section': f'Section {section} already exists for term {term.name}.'
                })
        
        return data
