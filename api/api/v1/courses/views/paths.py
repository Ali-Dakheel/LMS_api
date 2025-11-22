"""
CoursePath ViewSet
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Q
from django.utils import timezone

from apps.courses.models import CoursePath
from api.v1.courses.serializers.paths import (
    CoursePathListSerializer,
    CoursePathDetailSerializer,
    CoursePathCreateUpdateSerializer,
)
from api.v1.courses.filters import CoursePathFilter
from api.v1.courses.permissions import IsOwnerOrAdmin
from api.v1.courses.validators import (
    validate_path_dates,
    validate_scope_consistency,
)
from core.responses import success_response, error_response
from core.pagination import StandardResultsSetPagination
from core.permissions import IsAdminOrTeacher


class CoursePathViewSet(viewsets.ModelViewSet):
    """
    ViewSet for CoursePath management.
    
    Supports 4 scopes:
    - course: All students
    - teacher: Teacher's personal prep
    - student: Personalized student path
    - offering: Section-specific content
    
    Permissions:
    - List/Retrieve: All authenticated users (filtered by scope)
    - Create: Admin/Teacher
    - Update: Admin or owner
    - Delete: Admin only
    """
    
    queryset = CoursePath.objects.select_related(
        'course',
        'course__subject',
        'teacher',
        'student',
        'offering',
        'source_book'
    ).all()
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = CoursePathFilter
    search_fields = ['label', 'description']
    ordering_fields = ['label', 'start_date', 'created_at']
    ordering = ['-start_date']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return CoursePathListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return CoursePathCreateUpdateSerializer
        return CoursePathDetailSerializer
    
    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        elif self.action in ['create']:
            return [IsAuthenticated(), IsAdminOrTeacher()]
        elif self.action in ['update', 'partial_update']:
            return [IsAuthenticated(), IsOwnerOrAdmin()]
        elif self.action in ['destroy']:
            return [IsAuthenticated(), IsAdminOrTeacher()]
        return [IsAuthenticated(), IsAdminOrTeacher()]
    
    def get_queryset(self):
        """Filter paths based on user role and scope."""
        queryset = super().get_queryset()
        user = self.request.user
        
        if not user or not user.is_authenticated:
            return queryset.filter(is_published=True, scope='course')
        
        if user.role == 'admin':
            return queryset
        
        # Filter by scope and user role
        if user.role == 'teacher':
            return queryset.for_teacher(user)
        elif user.role == 'student':
            return queryset.for_student(user)
        
        # Default: only published course-level paths
        return queryset.filter(is_published=True, scope='course')
    
    def list(self, request, *args, **kwargs):
        """List paths accessible to user."""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return success_response(
            data=serializer.data,
            message="Paths retrieved successfully"
        )
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve a single path."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(
            data=serializer.data,
            message="Path retrieved successfully"
        )
    
    def create(self, request, *args, **kwargs):
        """Create a new path."""
        try:
            validate_scope_consistency(request.data)
            validate_path_dates(request.data)
        except ValidationError as e:
            return error_response(
                message="Validation error",
                errors=e.detail if hasattr(e, 'detail') else str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        return success_response(
            data=serializer.data,
            message="Path created successfully",
            status_code=status.HTTP_201_CREATED
        )
    
    def update(self, request, *args, **kwargs):
        """Update a path."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Check permission
        self.check_object_permissions(request, instance)
        
        try:
            validate_scope_consistency({**request.data, 'scope': instance.scope})
            validate_path_dates({**request.data})
        except ValidationError as e:
            return error_response(
                message="Validation error",
                errors=e.detail if hasattr(e, 'detail') else str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=partial
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return success_response(
            data=serializer.data,
            message="Path updated successfully"
        )
    
    def destroy(self, request, *args, **kwargs):
        """Delete a path."""
        instance = self.get_object()
        self.perform_destroy(instance)
        
        return success_response(
            message="Path deleted successfully",
            status_code=status.HTTP_204_NO_CONTENT
        )
    
    @action(detail=False, methods=['get'])
    def my_paths(self, request):
        """Get paths created/owned by current user."""
        user = request.user
        
        if user.role == 'teacher':
            paths = self.get_queryset().filter(
                Q(teacher=user) | Q(scope='course')
            ).distinct()
        elif user.role == 'student':
            paths = self.get_queryset().filter(
                Q(student=user) | Q(scope='course')
            ).distinct()
        else:
            paths = self.get_queryset()
        
        page = self.paginate_queryset(paths)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(paths, many=True)
        return success_response(
            data=serializer.data,
            message="Your paths retrieved successfully"
        )
    
    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        """Publish a path (admin/owner only)."""
        path = self.get_object()
        self.check_object_permissions(request, path)
        
        # Check if all modules are published
        unpublished = path.modules.filter(is_published=False).count()
        if unpublished > 0:
            return error_response(
                message=f"Cannot publish path: {unpublished} unpublished modules",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        if not path.modules.exists():
            return error_response(
                message="Cannot publish path: No modules defined",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        path.is_published = True
        path.published_at = timezone.now()
        path.save()
        
        serializer = self.get_serializer(path)
        return success_response(
            data=serializer.data,
            message="Path published successfully"
        )