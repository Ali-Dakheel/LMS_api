"""
User Management ViewSet (Admin Only) - Complete

Handles:
- List users with filtering/search/ordering
- Create new users
- Retrieve user details
- Update users
- Deactivate/reactivate users
- Role-specific user lists (teachers, students, deans)
"""

import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.users.models import User
from core.responses import success_response, error_response
from core.permissions import IsAdmin, IsAdminTeacherOrDean, IsAdminOrDean
from ..serializers import (
    UserListSerializer,
    UserDetailSerializer,
    UserCreateUpdateSerializer,
)
from ..filters import UserFilter

logger = logging.getLogger(__name__)


class UserViewSet(viewsets.ModelViewSet):
    """
    User management ViewSet (admin primary, some actions multi-role).
    
    Standard endpoints:
        GET    /api/v1/users/           -> list (Admin only)
        POST   /api/v1/users/           -> create (Admin only)
        GET    /api/v1/users/{id}/      -> retrieve (Admin only)
        PUT    /api/v1/users/{id}/      -> update (Admin only)
        PATCH  /api/v1/users/{id}/      -> partial_update (Admin only)
        DELETE /api/v1/users/{id}/      -> destroy (Admin only, soft delete)
    
    Custom actions:
        POST   /api/v1/users/{id}/reactivate/ -> reactivate (Admin only)
        GET    /api/v1/users/teachers/        -> teachers (Admin/Teacher/Dean)
        GET    /api/v1/users/students/        -> students (Admin/Teacher/Dean)
        GET    /api/v1/users/deans/           -> deans (Admin/Dean only)
    
    Features:
        - Filtering (role, status, dates, academic level)
        - Search (email, name, institution)
        - Ordering (created_at, name, email, last_login)
        - Pagination (default page size: 20)
    """
    
    permission_classes = [IsAdmin]  # Default permission
    queryset = User.objects.all().select_related('teacher_info', 'student_info')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = UserFilter
    search_fields = ['email', 'name', 'institution']
    ordering_fields = ['created_at', 'name', 'email', 'last_login_at']
    ordering = ['-created_at']
    
    def get_permissions(self):
        """
        Set permissions dynamically based on action.
        
        Permissions:
            - Admin only: list, create, update, destroy, reactivate
            - Admin/Teacher/Dean: teachers, students
            - Admin/Dean: deans
        """
        if self.action in ['teachers', 'students']:
            permission_classes = [IsAdminTeacherOrDean]
        elif self.action == 'deans':
            permission_classes = [IsAdminOrDean]
        else:
            permission_classes = [IsAdmin]
        
        return [permission() for permission in permission_classes]
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return UserListSerializer
        elif self.action == 'retrieve':
            return UserDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return UserCreateUpdateSerializer
        return UserDetailSerializer
    
    def get_queryset(self):
        """Optimize queryset with select_related for related objects."""
        queryset = super().get_queryset()
        # Base queryset already has select_related
        return queryset
    
    # =========================================================================
    # STANDARD CRUD OPERATIONS
    # =========================================================================
    
    def list(self, request, *args, **kwargs):
        """
        List all users with filtering, search, and pagination (K-12 Focus).

        Query parameters:
            - role: Filter by role (admin/dean/teacher/student)
            - is_active: Filter by active status (true/false)
            - email_verified: Filter by email verification (true/false)
            - created_after: Filter users created after date
            - created_before: Filter users created before date
            - student_status: Filter students by status
            - search: Search in email, name, institution
            - ordering: Sort by field (prefix with - for descending)
            - page: Page number
            - page_size: Items per page (default: 20)
        """
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        
        logger.info(
            f"Admin {request.user.id} listed {queryset.count()} users"
        )
        
        return success_response(
            data=serializer.data,
            message="Users retrieved successfully",
            status_code=status.HTTP_200_OK
        )
    
    def create(self, request, *args, **kwargs):
        """
        Create new user.
        
        Required fields vary by role:
            - Admin: email, name, password
            - Dean: email, name, password (academic fields optional)
            - Teacher: email, name, password, institution, department, teacher_info
            - Student: email, name, password, institution, department, major
        
        Note: User profiles (TeacherInfo/StudentInfo) auto-created via signals.
        """
        serializer = self.get_serializer(data=request.data)
        
        if not serializer.is_valid():
            logger.warning(
                f"User creation failed by admin {request.user.id}: "
                f"{serializer.errors}"
            )
            return error_response(
                message="User creation failed",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        user = serializer.save()
        
        logger.info(
            f"User created by admin {request.user.id}: "
            f"{user.id} ({user.email}, role: {user.role})"
        )
        
        return success_response(
            data=UserDetailSerializer(user).data,
            message="User created successfully",
            status_code=status.HTTP_201_CREATED
        )
    
    def retrieve(self, request, *args, **kwargs):
        """
        Get detailed user information.
        
        Returns:
            - All user fields
            - Role-specific info (teacher_info or student_info)
            - Activity tracking data
            - Account status
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        return success_response(
            data=serializer.data,
            message="User retrieved successfully",
            status_code=status.HTTP_200_OK
        )
    
    def update(self, request, *args, **kwargs):
        """
        Update user (full or partial).
        
        Supports:
            - PUT: Full update (all fields required)
            - PATCH: Partial update (only provided fields updated)
        
        Note: Password optional on update (set to change).
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=partial
        )
        
        if not serializer.is_valid():
            logger.warning(
                f"User update failed by admin {request.user.id} "
                f"for user {instance.id}: {serializer.errors}"
            )
            return error_response(
                message="User update failed",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        user = serializer.save()
        
        logger.info(
            f"User {user.id} updated by admin {request.user.id}: "
            f"{list(request.data.keys())}"
        )
        
        return success_response(
            data=UserDetailSerializer(user).data,
            message="User updated successfully",
            status_code=status.HTTP_200_OK
        )
    
    def destroy(self, request, *args, **kwargs):
        """
        Deactivate user (soft delete).
        
        Actions performed:
            - Sets is_active=False
            - Records deactivation timestamp and reason
            - Blacklists all JWT tokens
            - Drops active enrollments (students)
            - Removes primary teacher status (teachers/deans)
        
        Note: User data is preserved (not deleted from database).
        """
        instance = self.get_object()
        
        # Prevent self-deactivation
        if instance.id == request.user.id:
            return error_response(
                message="Cannot deactivate your own account",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        reason = request.data.get('reason', 'Deactivated by admin')
        instance.deactivate(reason=reason)
        
        logger.warning(
            f"User {instance.id} ({instance.email}) deactivated "
            f"by admin {request.user.id}. Reason: {reason}"
        )
        
        return success_response(
            message="User deactivated successfully",
            status_code=status.HTTP_200_OK
        )
    
    # =========================================================================
    # CUSTOM ACTIONS
    # =========================================================================
    
    @action(detail=True, methods=['post'])
    def reactivate(self, request, pk=None):
        """
        Reactivate a deactivated user.
        
        Endpoint: POST /api/v1/users/{id}/reactivate/
        Permission: Admin only
        
        Actions:
            - Sets is_active=True
            - Clears deactivation timestamp and reason
        
        Note: Does not restore enrollments or assignments
        (must be manually reassigned).
        """
        user = self.get_object()
        
        if user.is_active:
            return error_response(
                message="User is already active",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        user.reactivate()
        
        logger.info(
            f"User {user.id} ({user.email}) reactivated "
            f"by admin {request.user.id}"
        )
        
        return success_response(
            data=UserDetailSerializer(user).data,
            message="User reactivated successfully",
            status_code=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['get'])
    def teachers(self, request):
        """
        Get all active teachers.
        
        Endpoint: GET /api/v1/users/teachers/
        Permission: Admin, Teacher, or Dean
        
        Use cases:
            - Deans: Oversee teaching staff
            - Teachers: View colleagues for collaboration
            - Admin: Manage teacher accounts
        
        Features:
            - Filtered to role='teacher' and is_active=True
            - Includes teacher_info (designation, specialization, level)
            - Supports pagination
        """
        queryset = User.objects.get_teachers()
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = UserListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = UserListSerializer(queryset, many=True)
        
        logger.info(
            f"User {request.user.id} ({request.user.role}) "
            f"listed {queryset.count()} teachers"
        )
        
        return success_response(
            data=serializer.data,
            message="Teachers retrieved successfully",
            status_code=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['get'])
    def students(self, request):
        """
        Get all active students.
        
        Endpoint: GET /api/v1/users/students/
        Permission: Admin, Teacher, or Dean
        
        Use cases:
            - Deans: Student affairs, admissions oversight
            - Teachers: View students for courses, grading
            - Admin: Manage student accounts
        
        Features:
            - Filtered to role='student' and is_active=True
            - Includes student_info (status, enrollment number)
            - Supports pagination
        """
        queryset = User.objects.get_students()
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = UserListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = UserListSerializer(queryset, many=True)
        
        logger.info(
            f"User {request.user.id} ({request.user.role}) "
            f"listed {queryset.count()} students"
        )
        
        return success_response(
            data=serializer.data,
            message="Students retrieved successfully",
            status_code=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['get'])
    def deans(self, request):
        """
        Get all active deans.
        
        Endpoint: GET /api/v1/users/deans/
        Permission: Admin or Dean only
        
        Use cases:
            - Deans: Coordinate with other deans across faculties
            - Admin: Manage leadership
        
        Note: Teachers cannot view deans (organizational hierarchy).
        
        Features:
            - Filtered to role='dean' and is_active=True
            - Includes teacher_info (deans can also teach)
            - Supports pagination
        """
        queryset = User.objects.get_deans()
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = UserListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = UserListSerializer(queryset, many=True)
        
        logger.info(
            f"User {request.user.id} ({request.user.role}) "
            f"listed {queryset.count()} deans"
        )
        
        return success_response(
            data=serializer.data,
            message="Deans retrieved successfully",
            status_code=status.HTTP_200_OK
        )