"""
Academic Assignment Views - K-12 Focus

ViewSets for TeacherTerm, TeacherSubject, StudentSection, StudentSubject
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.academics.models import (
    TeacherTerm,
    TeacherSubject,
    StudentSection,
    StudentSubject,
)
from ..serializers import (
    TeacherTermSerializer,
    TeacherSubjectSerializer,
    StudentSectionSerializer,
    StudentSubjectSerializer,
)
from core.permissions import IsAdminOrDean
from core.responses import success_response, error_response
from core.pagination import StandardResultsSetPagination


class TeacherTermViewSet(viewsets.ModelViewSet):
    """
    ViewSet for TeacherTerm (Grade Assignments) - K-12 Focus.

    Permissions:
    - List/Retrieve: Admin, Dean, Teacher (their own)
    - Create/Update/Delete: Admin, Dean only
    """

    queryset = TeacherTerm.objects.select_related('teacher', 'term').all()
    serializer_class = TeacherTermSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['teacher__name', 'term__name']
    ordering_fields = ['assigned_at']
    ordering = ['-assigned_at']

    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        return [IsAdminOrDean()]

    def get_queryset(self):
        """Filter based on user role and query params."""
        queryset = super().get_queryset()
        user = self.request.user

        teacher_id = self.request.query_params.get('teacher')
        term_id = self.request.query_params.get('term')
        is_active = self.request.query_params.get('is_active')

        # Teachers see only their own assignments
        if user.role == 'teacher':
            queryset = queryset.filter(teacher=user)

        if teacher_id:
            queryset = queryset.filter(teacher_id=teacher_id)
        if term_id:
            queryset = queryset.filter(term_id=term_id)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        return queryset

    def list(self, request, *args, **kwargs):
        """List teacher term assignments with pagination."""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return success_response(
            data=serializer.data,
            message="Teacher term assignments retrieved successfully"
        )

    def retrieve(self, request, *args, **kwargs):
        """Retrieve a single teacher term assignment."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(
            data=serializer.data,
            message="Teacher term assignment retrieved successfully"
        )

    def create(self, request, *args, **kwargs):
        """Create a new teacher term assignment."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        return success_response(
            data=serializer.data,
            message="Teacher assigned to term successfully",
            status_code=status.HTTP_201_CREATED
        )

    def update(self, request, *args, **kwargs):
        """Update a teacher term assignment."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return success_response(
            data=serializer.data,
            message="Teacher term assignment updated successfully"
        )

    def destroy(self, request, *args, **kwargs):
        """Soft delete (deactivate) a teacher term assignment."""
        instance = self.get_object()
        instance.is_active = False
        instance.save()

        return success_response(
            message="Teacher term assignment deactivated successfully",
            status_code=status.HTTP_204_NO_CONTENT
        )

    @action(detail=False, methods=['get'])
    def my_terms(self, request):
        """Get terms assigned to current teacher."""
        if request.user.role != 'teacher':
            return error_response(
                message='Only teachers can access their term assignments',
                error_code='PERMISSION_DENIED',
                status_code=status.HTTP_403_FORBIDDEN
            )

        assignments = self.queryset.filter(teacher=request.user, is_active=True)
        serializer = self.get_serializer(assignments, many=True)
        return success_response(
            data=serializer.data,
            message="Your term assignments retrieved successfully"
        )


class TeacherSubjectViewSet(viewsets.ModelViewSet):
    """
    ViewSet for TeacherSubject - K-12 Focus.

    Permissions:
    - List/Retrieve: Admin, Dean, Teacher (their own)
    - Create/Update/Delete: Admin, Dean only
    """

    queryset = TeacherSubject.objects.select_related('teacher', 'subject').all()
    serializer_class = TeacherSubjectSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['teacher__name', 'subject__name']
    ordering_fields = ['assigned_at']
    ordering = ['-assigned_at']

    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        return [IsAdminOrDean()]

    def get_queryset(self):
        """Filter based on user role and query params."""
        queryset = super().get_queryset()
        user = self.request.user

        teacher_id = self.request.query_params.get('teacher')
        subject_id = self.request.query_params.get('subject')

        # Teachers see only their own assignments
        if user.role == 'teacher':
            queryset = queryset.filter(teacher=user)

        if teacher_id:
            queryset = queryset.filter(teacher_id=teacher_id)
        if subject_id:
            queryset = queryset.filter(subject_id=subject_id)

        return queryset

    def list(self, request, *args, **kwargs):
        """List teacher subject assignments with pagination."""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return success_response(
            data=serializer.data,
            message="Teacher subject assignments retrieved successfully"
        )

    def retrieve(self, request, *args, **kwargs):
        """Retrieve a single teacher subject assignment."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(
            data=serializer.data,
            message="Teacher subject assignment retrieved successfully"
        )

    def create(self, request, *args, **kwargs):
        """Create a new teacher subject assignment."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        return success_response(
            data=serializer.data,
            message="Teacher assigned to subject successfully",
            status_code=status.HTTP_201_CREATED
        )

    def update(self, request, *args, **kwargs):
        """Update a teacher subject assignment."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return success_response(
            data=serializer.data,
            message="Teacher subject assignment updated successfully"
        )

    def destroy(self, request, *args, **kwargs):
        """Delete a teacher subject assignment."""
        instance = self.get_object()
        self.perform_destroy(instance)

        return success_response(
            message="Teacher subject assignment deleted successfully",
            status_code=status.HTTP_204_NO_CONTENT
        )

    @action(detail=False, methods=['get'])
    def my_subjects(self, request):
        """Get subjects assigned to current teacher."""
        if request.user.role != 'teacher':
            return error_response(
                message='Only teachers can access their subject assignments',
                error_code='PERMISSION_DENIED',
                status_code=status.HTTP_403_FORBIDDEN
            )

        assignments = self.queryset.filter(teacher=request.user)
        serializer = self.get_serializer(assignments, many=True)
        return success_response(
            data=serializer.data,
            message="Your subject assignments retrieved successfully"
        )


class StudentSectionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for StudentSection (Homeroom Assignments) - K-12 Focus.

    Permissions:
    - List/Retrieve: Admin, Dean, Teacher, Student (their own)
    - Create/Update/Delete: Admin, Dean only
    """

    queryset = StudentSection.objects.select_related('student', 'class_section').all()
    serializer_class = StudentSectionSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['student__name', 'class_section__name']
    ordering_fields = ['enrolled_at']
    ordering = ['-enrolled_at']

    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        return [IsAdminOrDean()]

    def get_queryset(self):
        """Filter based on user role and query params."""
        queryset = super().get_queryset()
        user = self.request.user

        student_id = self.request.query_params.get('student')
        section_id = self.request.query_params.get('section')

        # Students see only their own section
        if user.role == 'student':
            queryset = queryset.filter(student=user)

        if student_id:
            queryset = queryset.filter(student_id=student_id)
        if section_id:
            queryset = queryset.filter(class_section_id=section_id)

        return queryset

    def list(self, request, *args, **kwargs):
        """List student sections with pagination."""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return success_response(
            data=serializer.data,
            message="Student sections retrieved successfully"
        )

    def retrieve(self, request, *args, **kwargs):
        """Retrieve a single student section."""
        instance = self.get_object()

        # Students can only view their own
        if request.user.role == 'student' and instance.student != request.user:
            return error_response(
                message='You can only view your own section',
                error_code='PERMISSION_DENIED',
                status_code=status.HTTP_403_FORBIDDEN
            )

        serializer = self.get_serializer(instance)
        return success_response(
            data=serializer.data,
            message="Student section retrieved successfully"
        )

    def create(self, request, *args, **kwargs):
        """Create a new student section assignment."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        return success_response(
            data=serializer.data,
            message="Student assigned to section successfully",
            status_code=status.HTTP_201_CREATED
        )

    def update(self, request, *args, **kwargs):
        """Update a student section."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return success_response(
            data=serializer.data,
            message="Student section updated successfully"
        )

    def destroy(self, request, *args, **kwargs):
        """Delete a student section assignment."""
        instance = self.get_object()
        self.perform_destroy(instance)

        return success_response(
            message="Student section assignment deleted successfully",
            status_code=status.HTTP_204_NO_CONTENT
        )

    @action(detail=False, methods=['get'])
    def my_section(self, request):
        """Get current student's section."""
        if request.user.role != 'student':
            return error_response(
                message='Only students can access their section',
                error_code='PERMISSION_DENIED',
                status_code=status.HTTP_403_FORBIDDEN
            )

        section = self.queryset.filter(student=request.user).first()

        if not section:
            return error_response(
                message='No section found',
                error_code='NOT_FOUND',
                status_code=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(section)
        return success_response(
            data=serializer.data,
            message="Your section retrieved successfully"
        )


class StudentSubjectViewSet(viewsets.ModelViewSet):
    """
    ViewSet for StudentSubject - K-12 Focus.

    Permissions:
    - List/Retrieve: Admin, Dean, Teacher, Student (their own)
    - Create/Update/Delete: Admin, Dean only
    """

    queryset = StudentSubject.objects.select_related('student', 'subject', 'term').all()
    serializer_class = StudentSubjectSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['student__name', 'subject__name']
    ordering_fields = ['assigned_at']
    ordering = ['-assigned_at']

    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        return [IsAdminOrDean()]

    def get_queryset(self):
        """Filter based on user role and query params."""
        queryset = super().get_queryset()
        user = self.request.user

        student_id = self.request.query_params.get('student')
        subject_id = self.request.query_params.get('subject')
        term_id = self.request.query_params.get('term')
        is_active = self.request.query_params.get('is_active')

        # Students see only their own subjects
        if user.role == 'student':
            queryset = queryset.filter(student=user)

        if student_id:
            queryset = queryset.filter(student_id=student_id)
        if subject_id:
            queryset = queryset.filter(subject_id=subject_id)
        if term_id:
            queryset = queryset.filter(term_id=term_id)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        return queryset

    def list(self, request, *args, **kwargs):
        """List student subjects with pagination."""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return success_response(
            data=serializer.data,
            message="Student subjects retrieved successfully"
        )

    def retrieve(self, request, *args, **kwargs):
        """Retrieve a single student subject."""
        instance = self.get_object()

        # Students can only view their own
        if request.user.role == 'student' and instance.student != request.user:
            return error_response(
                message='You can only view your own subjects',
                error_code='PERMISSION_DENIED',
                status_code=status.HTTP_403_FORBIDDEN
            )

        serializer = self.get_serializer(instance)
        return success_response(
            data=serializer.data,
            message="Student subject retrieved successfully"
        )

    def create(self, request, *args, **kwargs):
        """Create a new student subject enrollment."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        return success_response(
            data=serializer.data,
            message="Student enrolled in subject successfully",
            status_code=status.HTTP_201_CREATED
        )

    def update(self, request, *args, **kwargs):
        """Update a student subject."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return success_response(
            data=serializer.data,
            message="Student subject updated successfully"
        )

    def destroy(self, request, *args, **kwargs):
        """Delete a student subject enrollment."""
        instance = self.get_object()
        self.perform_destroy(instance)

        return success_response(
            message="Student subject enrollment deleted successfully",
            status_code=status.HTTP_204_NO_CONTENT
        )

    @action(detail=False, methods=['get'])
    def my_subjects(self, request):
        """Get current student's subjects."""
        if request.user.role != 'student':
            return error_response(
                message='Only students can access their subjects',
                error_code='PERMISSION_DENIED',
                status_code=status.HTTP_403_FORBIDDEN
            )

        subjects = self.queryset.filter(student=request.user, is_active=True)
        serializer = self.get_serializer(subjects, many=True)
        return success_response(
            data=serializer.data,
            message="Your subjects retrieved successfully"
        )
