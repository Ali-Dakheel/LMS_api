"""
Enrollment Views

ViewSets for Enrollment, EnrollmentWaitlist, StudentEligibility
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.academics.models import (
    Enrollment,
    EnrollmentWaitlist,
    StudentEligibility,
)
from ..serializers import (
    EnrollmentListSerializer,
    EnrollmentDetailSerializer,
    EnrollmentCreateSerializer,
    EnrollmentWaitlistSerializer,
    StudentEligibilitySerializer,
)
from ..filters import EnrollmentFilter
from core.permissions import IsAdminOrDean, IsAdminOrTeacher, IsStudent
from core.responses import success_response, error_response
from core.pagination import StandardResultsSetPagination
from django.utils import timezone


class EnrollmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Enrollment.
    
    Permissions:
    - List: Admin, Dean, Teacher (their offerings), Student (their own)
    - Retrieve: Admin, Dean, Teacher (their offerings), Student (their own)
    - Create: Admin, Dean, Student (self-enrollment if allowed)
    - Update/Delete: Admin, Dean only
    """
    
    queryset = Enrollment.objects.select_related(
        'student',
        'offering',
        'offering__course',
        'offering__term'
    ).all()
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = EnrollmentFilter
    search_fields = ['student__name', 'student__email', 'offering__course__title']
    ordering_fields = ['enrolled_at', 'created_at']
    ordering = ['-enrolled_at']
    
    def get_serializer_class(self):
        """Use different serializers based on action."""
        if self.action == 'create':
            return EnrollmentCreateSerializer
        elif self.action == 'list':
            return EnrollmentListSerializer
        return EnrollmentDetailSerializer
    
    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        elif self.action == 'create':
            return [IsAuthenticated()]  # Students can self-enroll
        return [IsAdminOrDean()]
    
    def get_queryset(self):
        """Filter enrollments based on user role."""
        queryset = super().get_queryset()
        user = self.request.user
        
        # Students see only their own enrollments
        if user.role == 'student':
            return queryset.filter(student=user)
        
        # Teachers see enrollments for their offerings
        elif user.role == 'teacher':
            return queryset.filter(offering__teachers__teacher=user).distinct()
        
        # Admin/Dean see all
        return queryset
    
    def list(self, request, *args, **kwargs):
        """List enrollments with pagination."""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return success_response(
            data=serializer.data,
            message="Enrollments retrieved successfully"
        )
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve a single enrollment."""
        instance = self.get_object()
        
        # Check permission: only own enrollment for students
        if request.user.role == 'student' and instance.student != request.user:
            return error_response(
                message='You can only view your own enrollments',
                error_code='PERMISSION_DENIED',
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(instance)
        return success_response(
            data=serializer.data,
            message="Enrollment retrieved successfully"
        )
    
    def create(self, request, *args, **kwargs):
        """Create a new enrollment (enroll student in offering)."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # If student is enrolling themselves
        if request.user.role == 'student':
            if serializer.validated_data['student'] != request.user:
                return error_response(
                    message='You can only enroll yourself',
                    error_code='PERMISSION_DENIED',
                    status_code=status.HTTP_403_FORBIDDEN
                )
        
        self.perform_create(serializer)
        
        return success_response(
            data=EnrollmentDetailSerializer(serializer.instance).data,
            message="Enrollment created successfully",
            status_code=status.HTTP_201_CREATED
        )
    
    def update(self, request, *args, **kwargs):
        """Update an enrollment."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        serializer = EnrollmentDetailSerializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return success_response(
            data=serializer.data,
            message="Enrollment updated successfully"
        )
    
    def destroy(self, request, *args, **kwargs):
        """Delete (withdraw) an enrollment."""
        instance = self.get_object()
        self.perform_destroy(instance)
        
        return success_response(
            message="Enrollment deleted successfully",
            status_code=status.HTTP_204_NO_CONTENT
        )
    
    @action(detail=False, methods=['get'])
    def my_enrollments(self, request):
        """Get current user's enrollments."""
        if request.user.role != 'student':
            return error_response(
                message='Only students can access their enrollments',
                error_code='PERMISSION_DENIED',
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        enrollments = self.queryset.filter(student=request.user, status='active')
        serializer = self.get_serializer(enrollments, many=True)
        
        return success_response(
            data=serializer.data,
            message="Your enrollments retrieved successfully"
        )
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get all active enrollments."""
        enrollments = self.get_queryset().filter(status='active')
        
        page = self.paginate_queryset(enrollments)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(enrollments, many=True)
        return success_response(
            data=serializer.data,
            message="Active enrollments retrieved successfully"
        )
    
    @action(detail=True, methods=['post'])
    def drop(self, request, pk=None):
        """Drop an enrollment (change status to dropped)."""
        enrollment = self.get_object()
        
        # Students can only drop their own enrollments
        if request.user.role == 'student' and enrollment.student != request.user:
            return error_response(
                message='You can only drop your own enrollments',
                error_code='PERMISSION_DENIED',
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        enrollment.status = 'dropped'
        enrollment.dropped_at = timezone.now()
        enrollment.save()
        
        serializer = self.get_serializer(enrollment)
        return success_response(
            data=serializer.data,
            message="Enrollment dropped successfully"
        )
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark enrollment as completed (admin/dean only)."""
        enrollment = self.get_object()
        final_grade = request.data.get('final_grade')
        
        enrollment.status = 'completed'
        enrollment.completed_at = timezone.now()
        
        if final_grade is not None:
            enrollment.final_grade = final_grade
        
        enrollment.save()
        
        serializer = self.get_serializer(enrollment)
        return success_response(
            data=serializer.data,
            message="Enrollment marked as completed"
        )
    
    @action(detail=True, methods=['post'])
    def withdraw(self, request, pk=None):
        """Withdraw an enrollment (change status to withdrawn)."""
        enrollment = self.get_object()
        
        # Students can only withdraw their own enrollments
        if request.user.role == 'student' and enrollment.student != request.user:
            return error_response(
                message='You can only withdraw from your own enrollments',
                error_code='PERMISSION_DENIED',
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        enrollment.status = 'withdrawn'
        enrollment.save()
        
        serializer = self.get_serializer(enrollment)
        return success_response(
            data=serializer.data,
            message="Enrollment withdrawn successfully"
        )


class EnrollmentWaitlistViewSet(viewsets.ModelViewSet):
    """
    ViewSet for EnrollmentWaitlist.
    
    Permissions:
    - List/Retrieve: Admin, Dean, Student (their own)
    - Create: Admin, Dean, Student (add themselves)
    - Delete: Admin, Dean, Student (remove themselves)
    """
    
    queryset = EnrollmentWaitlist.objects.select_related(
        'student',
        'offering',
        'offering__course'
    ).all()
    serializer_class = EnrollmentWaitlistSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    ordering_fields = ['position', 'added_at']
    ordering = ['position']
    
    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['list', 'retrieve', 'create', 'destroy']:
            return [IsAuthenticated()]
        return [IsAdminOrDean()]
    
    def get_queryset(self):
        """Filter waitlist based on user role."""
        queryset = super().get_queryset()
        user = self.request.user
        offering_id = self.request.query_params.get('offering')
        
        if offering_id:
            queryset = queryset.filter(offering_id=offering_id)
        
        # Students see only their own waitlist entries
        if user.role == 'student':
            return queryset.filter(student=user)
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        """List waitlist entries with pagination."""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return success_response(
            data=serializer.data,
            message="Waitlist entries retrieved successfully"
        )
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve a single waitlist entry."""
        instance = self.get_object()
        
        # Students can only view their own entries
        if request.user.role == 'student' and instance.student != request.user:
            return error_response(
                message='You can only view your own waitlist entries',
                error_code='PERMISSION_DENIED',
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(instance)
        return success_response(
            data=serializer.data,
            message="Waitlist entry retrieved successfully"
        )
    
    def create(self, request, *args, **kwargs):
        """Add student to waitlist."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Students can only add themselves
        if request.user.role == 'student':
            if serializer.validated_data['student'] != request.user:
                return error_response(
                    message='You can only add yourself to the waitlist',
                    error_code='PERMISSION_DENIED',
                    status_code=status.HTTP_403_FORBIDDEN
                )
        
        # Check if already on waitlist
        offering = serializer.validated_data['offering']
        student = serializer.validated_data['student']
        
        if EnrollmentWaitlist.objects.filter(offering=offering, student=student).exists():
            return error_response(
                message='You are already on the waitlist for this offering',
                error_code='ALREADY_EXISTS',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if already enrolled
        if Enrollment.objects.filter(offering=offering, student=student).exists():
            return error_response(
                message='You are already enrolled in this offering',
                error_code='ALREADY_ENROLLED',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        self.perform_create(serializer)
        
        return success_response(
            data=serializer.data,
            message="Added to waitlist successfully",
            status_code=status.HTTP_201_CREATED
        )
    
    def destroy(self, request, *args, **kwargs):
        """Remove from waitlist."""
        instance = self.get_object()
        
        # Students can only remove themselves
        if request.user.role == 'student' and instance.student != request.user:
            return error_response(
                message='You can only remove yourself from the waitlist',
                error_code='PERMISSION_DENIED',
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        self.perform_destroy(instance)
        
        return success_response(
            message="Removed from waitlist successfully",
            status_code=status.HTTP_204_NO_CONTENT
        )
    
    @action(detail=False, methods=['get'])
    def my_waitlist(self, request):
        """Get current user's waitlist entries."""
        if request.user.role != 'student':
            return error_response(
                message='Only students can access their waitlist',
                error_code='PERMISSION_DENIED',
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        waitlist = self.queryset.filter(student=request.user)
        serializer = self.get_serializer(waitlist, many=True)
        
        return success_response(
            data=serializer.data,
            message="Your waitlist entries retrieved successfully"
        )


class StudentEligibilityViewSet(viewsets.ModelViewSet):
    """
    ViewSet for StudentEligibility.
    
    Permissions:
    - List/Retrieve: Admin, Dean, Student (their own)
    - Create/Update: Admin, Dean only
    - Delete: Admin only
    """
    
    queryset = StudentEligibility.objects.select_related(
        'student',
        'course',
        'overridden_by'
    ).all()
    serializer_class = StudentEligibilitySerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['student__name', 'course__title']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        elif self.action in ['create', 'update', 'partial_update']:
            return [IsAdminOrDean()]
        return [IsAdminOrDean()]
    
    def get_queryset(self):
        """Filter eligibility based on user role."""
        queryset = super().get_queryset()
        user = self.request.user
        
        # Students see only their own eligibility
        if user.role == 'student':
            return queryset.filter(student=user)
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        """List eligibility records with pagination."""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return success_response(
            data=serializer.data,
            message="Eligibility records retrieved successfully"
        )
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve a single eligibility record."""
        instance = self.get_object()
        
        # Students can only view their own records
        if request.user.role == 'student' and instance.student != request.user:
            return error_response(
                message='You can only view your own eligibility records',
                error_code='PERMISSION_DENIED',
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(instance)
        return success_response(
            data=serializer.data,
            message="Eligibility record retrieved successfully"
        )
    
    def create(self, request, *args, **kwargs):
        """Create a new eligibility record (K-12 Focus)."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return success_response(
            data=serializer.data,
            message="Eligibility record created successfully",
            status_code=status.HTTP_201_CREATED
        )
    
    def update(self, request, *args, **kwargs):
        """Update an eligibility record."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return success_response(
            data=serializer.data,
            message="Eligibility record updated successfully"
        )
    
    def destroy(self, request, *args, **kwargs):
        """Delete an eligibility record."""
        instance = self.get_object()
        self.perform_destroy(instance)
        
        return success_response(
            message="Eligibility record deleted successfully",
            status_code=status.HTTP_204_NO_CONTENT
        )
    
    @action(detail=False, methods=['get'])
    def my_eligibility(self, request):
        """Get current user's eligibility records."""
        if request.user.role != 'student':
            return error_response(
                message='Only students can access their eligibility',
                error_code='PERMISSION_DENIED',
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        eligibility = self.queryset.filter(student=request.user)
        serializer = self.get_serializer(eligibility, many=True)
        
        return success_response(
            data=serializer.data,
            message="Your eligibility records retrieved successfully"
        )
    
    @action(detail=False, methods=['post'])
    def check_eligibility(self, request):
        """Check eligibility for a student and course."""
        student_id = request.data.get('student_id')
        course_id = request.data.get('course_id')
        
        if not student_id or not course_id:
            return error_response(
                message='student_id and course_id are required',
                error_code='MISSING_PARAMETER',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        from django.contrib.auth import get_user_model
        from apps.courses.models import Course
        
        User = get_user_model()
        
        try:
            student = User.objects.get(id=student_id, role='student')
            course = Course.objects.get(id=course_id)
        except (User.DoesNotExist, Course.DoesNotExist):
            return error_response(
                message='Student or course not found',
                error_code='NOT_FOUND',
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # K-12 Eligibility: Students are eligible if they're in the appropriate grade level
        # No prerequisite checking for K-12 - all students in a grade take grade-level courses

        is_eligible = True
        missing_prerequisites = []

        # TODO: Add grade-level matching logic if needed
        # For now, all students are eligible for courses in their grade

        eligibility_status = 'eligible' if is_eligible else 'not_eligible'

        # Create or update eligibility record
        eligibility, created = StudentEligibility.objects.update_or_create(
            student=student,
            course=course,
            defaults={
                'status': eligibility_status
            }
        )
        
        serializer = self.get_serializer(eligibility)
        
        return success_response(
            data={
                'eligibility': serializer.data,
                'is_eligible': is_eligible,
                'missing_prerequisites': missing_prerequisites
            },
            message=f"Eligibility checked: {'Approved' if is_eligible else 'Denied'}"
        )