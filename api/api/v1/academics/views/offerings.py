"""
Course Offering Views

ViewSets for CourseOffering, OfferingTeacher, ClassSession, Attendance
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.academics.models import (
    CourseOffering,
    OfferingTeacher,
    ClassSession,
    Attendance,
)
from ..serializers import (
    CourseOfferingListSerializer,
    CourseOfferingDetailSerializer,
    OfferingTeacherSerializer,
    ClassSessionSerializer,
    AttendanceSerializer,
    CourseOfferingWriteSerializer,
)
from ..filters import CourseOfferingFilter
from core.permissions import IsAdminOrDean, IsAdminOrStudent, IsAdminOrTeacher, IsStudent
from core.responses import success_response, error_response
from core.pagination import StandardResultsSetPagination
from ..permissions import IsOfferingTeacher, IsEnrolledStudent


class CourseOfferingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for CourseOffering.
    
    Permissions:
    - List/Retrieve: All authenticated users
    - Create/Update/Delete: Admin or Dean only
    - Custom actions: Role-specific
    """
    
    queryset = CourseOffering.objects.select_related(
        'course',
        'term',
        'class_section'
    ).prefetch_related('teachers').all()
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = CourseOfferingFilter
    search_fields = ['course__title', 'course__code', 'class_section__name']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Use different serializers based on action."""
        if self.action == 'list':
            return CourseOfferingListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return CourseOfferingWriteSerializer
        else:  # retrieve, destroy, custom actions
            return CourseOfferingDetailSerializer
    
    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        elif self.action in ['my_offerings']:
            return [IsAdminOrTeacher()]
        elif self.action in ['my_enrollments']:
            return [IsAdminOrStudent()]  
        return [IsAdminOrDean()]

        
    def get_queryset(self):
        """Filter queryset based on user role."""
        queryset = super().get_queryset()
        user = self.request.user
        
        # Students see only their enrolled offerings
        if user.role == 'student' and self.action == 'list':
            from apps.academics.models import Enrollment
            enrolled_offerings = Enrollment.objects.filter(
                student=user,
                status='active'
            ).values_list('offering_id', flat=True)
            return queryset.filter(id__in=enrolled_offerings)
        
        # Teachers see their assigned offerings
        elif user.role == 'teacher' and self.action == 'list':
            return queryset.filter(teachers__teacher=user, is_active=True)
        
        return queryset.filter(is_active=True)
    
    def list(self, request, *args, **kwargs):
        """List course offerings with pagination."""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return success_response(
            data=serializer.data,
            message="Course offerings retrieved successfully"
        )
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve a single course offering."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(
            data=serializer.data,
            message="Course offering retrieved successfully"
        )
    
    def create(self, request, *args, **kwargs):
        """Create a new course offering."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        return success_response(
            data=serializer.data,
            message="Course offering created successfully",
            status_code=status.HTTP_201_CREATED
        )
    
    def update(self, request, *args, **kwargs):
        """Update a course offering."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return success_response(
            data=serializer.data,
            message="Course offering updated successfully"
        )
    
    def destroy(self, request, *args, **kwargs):
        """Soft delete (deactivate) a course offering."""
        instance = self.get_object()
        instance.is_active = False
        instance.save()
        
        return success_response(
            message="Course offering deactivated successfully",
            status_code=status.HTTP_204_NO_CONTENT
        )
    
    @action(detail=False, methods=['get'])
    def my_offerings(self, request):
        """Get offerings for current teacher or admin."""
        user = request.user
        
        # Allow teachers and admins
        if user.role not in ['teacher', 'admin']:
            return error_response(
                message='Only teachers and admins can access offerings',
                error_code='PERMISSION_DENIED',
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        # If admin, show all offerings; if teacher, show only theirs
        if user.role == 'admin':
            offerings = self.queryset.filter(is_active=True)
        else:  # teacher
            offerings = self.queryset.filter(
                teachers__teacher=user,
                is_active=True
            ).distinct()
        
        serializer = self.get_serializer(offerings, many=True)
        return success_response(
            data=serializer.data,
            message="Course offerings retrieved successfully"
        )
    
    @action(detail=False, methods=['get'])
    def my_enrollments(self, request):
        """Get enrolled offerings for current student or admin."""
        user = request.user
        
        # Allow students and admins
        if user.role not in ['student', 'admin']:
            return error_response(
                message='Only students and admins can access enrollments',
                error_code='PERMISSION_DENIED',
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        from apps.academics.models import Enrollment
        
        if user.role == 'admin':
            # Admins see all active enrollments
            enrollments = Enrollment.objects.filter(status='active')
            offerings = self.queryset.filter(
                id__in=enrollments.values_list('offering_id', flat=True)
            )
        else:  # student
            enrolled_offerings = Enrollment.objects.filter(
                student=user,
                status='active'
            ).values_list('offering_id', flat=True)
            offerings = self.queryset.filter(id__in=enrolled_offerings)
        
        serializer = self.get_serializer(offerings, many=True)
        return success_response(
            data=serializer.data,
            message="Your enrolled courses retrieved successfully"
        )
        
    @action(detail=True, methods=['get'])
    def students(self, request, pk=None):
        """Get all enrolled students in this offering."""
        offering = self.get_object()
        
        # Check permission: teacher or admin
        if request.user.role not in ['admin', 'teacher']:
            return error_response(
                message='Only teachers and admins can view enrolled students',
                error_code='PERMISSION_DENIED',
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        from apps.academics.models import Enrollment
        enrollments = Enrollment.objects.filter(
            offering=offering,
            status='active'
        ).select_related('student')
        
        data = [{
            'id': e.student.id,
            'name': e.student.name,
            'email': e.student.email,
            'enrolled_at': e.enrolled_at,
            'status': e.status,
        } for e in enrollments]
        
        return success_response(
            data=data,
            message=f"Students enrolled in '{offering.course.title}' retrieved successfully"
        )
    
    @action(detail=True, methods=['post'])
    def assign_teacher(self, request, pk=None):
        """Assign a teacher to this offering."""
        offering = self.get_object()
        teacher_id = request.data.get('teacher_id')
        is_primary = request.data.get('is_primary', False)
        
        if not teacher_id:
            return error_response(
                message='teacher_id is required',
                error_code='MISSING_PARAMETER',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        try:
            teacher = User.objects.get(id=teacher_id, role='teacher')
        except User.DoesNotExist:
            return error_response(
                message='Teacher not found',
                error_code='NOT_FOUND',
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Check if already assigned
        if OfferingTeacher.objects.filter(offering=offering, teacher=teacher).exists():
            return error_response(
                message='Teacher is already assigned to this offering',
                error_code='ALREADY_EXISTS',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Create assignment
        offering_teacher = OfferingTeacher.objects.create(
            offering=offering,
            teacher=teacher,
            is_primary=is_primary
        )
        
        serializer = OfferingTeacherSerializer(offering_teacher)
        return success_response(
            data=serializer.data,
            message=f"Teacher '{teacher.name}' assigned successfully",
            status_code=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['delete'])
    def remove_teacher(self, request, pk=None):
        """Remove a teacher from this offering."""
        offering = self.get_object()
        teacher_id = request.data.get('teacher_id')
        
        if not teacher_id:
            return error_response(
                message='teacher_id is required',
                error_code='MISSING_PARAMETER',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            offering_teacher = OfferingTeacher.objects.get(
                offering=offering,
                teacher_id=teacher_id
            )
            offering_teacher.delete()
            
            return success_response(
                message="Teacher removed from offering successfully",
                status_code=status.HTTP_204_NO_CONTENT
            )
        except OfferingTeacher.DoesNotExist:
            return error_response(
                message='Teacher assignment not found',
                error_code='NOT_FOUND',
                status_code=status.HTTP_404_NOT_FOUND
            )


class ClassSessionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for ClassSession.
    
    Permissions:
    - List/Retrieve: Enrolled students, assigned teachers, admins
    - Create/Update/Delete: Assigned teachers, admins
    """
    
    queryset = ClassSession.objects.select_related('offering').all()
    serializer_class = ClassSessionSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['topic']
    ordering_fields = ['session_date', 'start_time']
    ordering = ['-session_date', 'start_time']
    
    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        return [IsAdminOrTeacher()]
    
    def get_queryset(self):
        """Filter sessions based on user role and offering."""
        queryset = super().get_queryset()
        user = self.request.user
        offering_id = self.request.query_params.get('offering')
        
        if offering_id:
            queryset = queryset.filter(offering_id=offering_id)
        
        # Students see sessions for enrolled offerings only
        if user.role == 'student':
            from apps.academics.models import Enrollment
            enrolled_offerings = Enrollment.objects.filter(
                student=user,
                status='active'
            ).values_list('offering_id', flat=True)
            queryset = queryset.filter(offering_id__in=enrolled_offerings)
        
        # Teachers see sessions for their offerings only
        elif user.role == 'teacher':
            queryset = queryset.filter(offering__teachers__teacher=user)
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        """List class sessions with pagination."""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return success_response(
            data=serializer.data,
            message="Class sessions retrieved successfully"
        )
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve a single class session."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(
            data=serializer.data,
            message="Class session retrieved successfully"
        )
    
    def create(self, request, *args, **kwargs):
        """Create a new class session."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        return success_response(
            data=serializer.data,
            message="Class session created successfully",
            status_code=status.HTTP_201_CREATED
        )
    
    def update(self, request, *args, **kwargs):
        """Update a class session."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return success_response(
            data=serializer.data,
            message="Class session updated successfully"
        )
    
    def destroy(self, request, *args, **kwargs):
        """Delete a class session."""
        instance = self.get_object()
        self.perform_destroy(instance)
        
        return success_response(
            message="Class session deleted successfully",
            status_code=status.HTTP_204_NO_CONTENT
        )
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a class session."""
        session = self.get_object()
        cancellation_reason = request.data.get('reason', '')
        
        session.is_cancelled = True
        session.cancellation_reason = cancellation_reason
        session.save()
        
        serializer = self.get_serializer(session)
        return success_response(
            data=serializer.data,
            message="Class session cancelled successfully"
        )
    
    @action(detail=True, methods=['post'])
    def uncancel(self, request, pk=None):
        """Uncancel a class session."""
        session = self.get_object()
        
        session.is_cancelled = False
        session.cancellation_reason = ''
        session.save()
        
        serializer = self.get_serializer(session)
        return success_response(
            data=serializer.data,
            message="Class session uncancelled successfully"
        )


class AttendanceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Attendance.
    
    Permissions:
    - List/Retrieve: Assigned teachers, admins, own student
    - Create/Update: Assigned teachers, admins
    - Delete: Admins only
    """
    
    queryset = Attendance.objects.select_related('class_session', 'student', 'marked_by').all()
    serializer_class = AttendanceSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    ordering_fields = ['created_at', 'class_session__session_date']
    ordering = ['-created_at']
    
    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        elif self.action in ['create', 'update', 'partial_update']:
            return [IsAdminOrTeacher()]
        return [IsAdminOrDean()]
    
    def get_queryset(self):
        """Filter attendance based on user role."""
        queryset = super().get_queryset()
        user = self.request.user
        session_id = self.request.query_params.get('session')
        student_id = self.request.query_params.get('student')

        if session_id:
            queryset = queryset.filter(class_session_id=session_id)
        if student_id:
            queryset = queryset.filter(student_id=student_id)

        # Students see only their own attendance
        if user.role == 'student':
            queryset = queryset.filter(student=user)

        # Teachers see attendance for their sessions only
        elif user.role == 'teacher':
            queryset = queryset.filter(class_session__offering__teachers__teacher=user)

        return queryset
    
    def list(self, request, *args, **kwargs):
        """List attendance records with pagination."""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return success_response(
            data=serializer.data,
            message="Attendance records retrieved successfully"
        )
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve a single attendance record."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(
            data=serializer.data,
            message="Attendance record retrieved successfully"
        )
    
    def create(self, request, *args, **kwargs):
        """Create a new attendance record."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Set marked_by to current user
        serializer.save(marked_by=request.user)
        
        return success_response(
            data=serializer.data,
            message="Attendance marked successfully",
            status_code=status.HTTP_201_CREATED
        )
    
    def update(self, request, *args, **kwargs):
        """Update an attendance record."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return success_response(
            data=serializer.data,
            message="Attendance record updated successfully"
        )
    
    def destroy(self, request, *args, **kwargs):
        """Delete an attendance record."""
        instance = self.get_object()
        self.perform_destroy(instance)
        
        return success_response(
            message="Attendance record deleted successfully",
            status_code=status.HTTP_204_NO_CONTENT
        )
    
    @action(detail=False, methods=['post'])
    def bulk_mark(self, request):
        """Bulk mark attendance for multiple students in a session."""
        session_id = request.data.get('session_id')
        attendance_records = request.data.get('attendance', [])  # [{'student_id': 1, 'status': 'present'}, ...]
        
        if not session_id or not attendance_records:
            return error_response(
                message='session_id and attendance records are required',
                error_code='MISSING_PARAMETER',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            session = ClassSession.objects.get(id=session_id)
        except ClassSession.DoesNotExist:
            return error_response(
                message='Session not found',
                error_code='NOT_FOUND',
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        created_records = []
        for record in attendance_records:
            attendance, created = Attendance.objects.update_or_create(
                class_session=session,
                student_id=record['student_id'],
                defaults={
                    'status': record['status'],
                    'marked_by': request.user,
                    'notes': record.get('notes', '')
                }
            )
            created_records.append(attendance)
        
        serializer = self.get_serializer(created_records, many=True)
        return success_response(
            data=serializer.data,
            message=f"Bulk attendance marked for {len(created_records)} students",
            status_code=status.HTTP_201_CREATED
        )


class OfferingTeacherViewSet(viewsets.ModelViewSet):
    """
    ViewSet for OfferingTeacher.

    Dedicated endpoint for managing teacher assignments to offerings.

    Permissions:
    - List/Retrieve: All authenticated users
    - Create/Update/Delete: Admin or Dean only
    """

    queryset = OfferingTeacher.objects.select_related('offering', 'teacher').all()
    serializer_class = OfferingTeacherSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = ['assigned_at', 'is_primary']
    ordering = ['-is_primary', '-assigned_at']

    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        return [IsAdminOrDean()]

    def get_queryset(self):
        """Filter by offering or teacher if specified."""
        queryset = super().get_queryset()
        offering_id = self.request.query_params.get('offering')
        teacher_id = self.request.query_params.get('teacher')

        if offering_id:
            queryset = queryset.filter(offering_id=offering_id)
        if teacher_id:
            queryset = queryset.filter(teacher_id=teacher_id)

        return queryset

    def list(self, request, *args, **kwargs):
        """List offering-teacher assignments with pagination."""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return success_response(
            data=serializer.data,
            message="Teacher assignments retrieved successfully"
        )

    def retrieve(self, request, *args, **kwargs):
        """Retrieve a single teacher assignment."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(
            data=serializer.data,
            message="Teacher assignment retrieved successfully"
        )

    def create(self, request, *args, **kwargs):
        """Create a new teacher assignment."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Validate teacher exists and has correct role
        teacher_id = serializer.validated_data.get('teacher').id
        from django.contrib.auth import get_user_model
        User = get_user_model()

        try:
            teacher = User.objects.get(id=teacher_id)
            if teacher.role != 'teacher':
                return error_response(
                    message='User must have teacher role',
                    error_code='INVALID_ROLE',
                    status_code=status.HTTP_400_BAD_REQUEST
                )
        except User.DoesNotExist:
            return error_response(
                message='Teacher not found',
                error_code='NOT_FOUND',
                status_code=status.HTTP_404_NOT_FOUND
            )

        self.perform_create(serializer)

        return success_response(
            data=serializer.data,
            message="Teacher assigned to offering successfully",
            status_code=status.HTTP_201_CREATED
        )

    def update(self, request, *args, **kwargs):
        """Update a teacher assignment (typically to change is_primary)."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return success_response(
            data=serializer.data,
            message="Teacher assignment updated successfully"
        )

    def destroy(self, request, *args, **kwargs):
        """Remove a teacher from an offering."""
        instance = self.get_object()
        offering_name = f"{instance.offering.course.title} - {instance.offering.class_section.name}"
        teacher_name = instance.teacher.name

        self.perform_destroy(instance)

        return success_response(
            message=f"Teacher '{teacher_name}' removed from '{offering_name}' successfully",
            status_code=status.HTTP_204_NO_CONTENT
        )

    @action(detail=False, methods=['post'])
    def set_primary(self, request):
        """Set a teacher as primary for an offering."""
        assignment_id = request.data.get('assignment_id')

        if not assignment_id:
            return error_response(
                message='assignment_id is required',
                error_code='MISSING_PARAMETER',
                status_code=status.HTTP_400_BAD_REQUEST
            )

        try:
            assignment = OfferingTeacher.objects.get(id=assignment_id)

            # Set all other teachers in this offering to non-primary
            OfferingTeacher.objects.filter(
                offering=assignment.offering,
                is_primary=True
            ).exclude(id=assignment_id).update(is_primary=False)

            # Set this teacher as primary
            assignment.is_primary = True
            assignment.save()

            serializer = self.get_serializer(assignment)
            return success_response(
                data=serializer.data,
                message=f"Teacher '{assignment.teacher.name}' set as primary"
            )
        except OfferingTeacher.DoesNotExist:
            return error_response(
                message='Assignment not found',
                error_code='NOT_FOUND',
                status_code=status.HTTP_404_NOT_FOUND
            )