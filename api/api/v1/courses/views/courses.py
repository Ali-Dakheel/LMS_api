"""
Course ViewSet
"""

from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.courses.models import Course
from api.v1.courses.serializers.courses import (
    CourseListSerializer,
    CourseDetailSerializer,
    CourseCreateUpdateSerializer,
)
from api.v1.courses.filters import CourseFilter
from api.v1.courses.permissions import IsAdminOrReadOnly
from core.responses import success_response
from core.pagination import StandardResultsSetPagination


class CourseViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Course management.
    
    Permissions:
    - List/Retrieve: All authenticated users
    - Create/Update/Delete: Admin only
    """
    
    queryset = Course.objects.select_related('subject').all()
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = CourseFilter
    search_fields = ['title', 'code']
    ordering_fields = ['title', 'created_at']
    ordering = ['title']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return CourseListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return CourseCreateUpdateSerializer
        return CourseDetailSerializer
    
    def list(self, request, *args, **kwargs):
        """List all courses with pagination."""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return success_response(
            data=serializer.data,
            message="Courses retrieved successfully"
        )
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve a single course."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(
            data=serializer.data,
            message="Course retrieved successfully"
        )
    
    def create(self, request, *args, **kwargs):
        """Create a new course."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        return success_response(
            data=serializer.data,
            message="Course created successfully",
            status_code=status.HTTP_201_CREATED
        )
    
    def update(self, request, *args, **kwargs):
        """Update a course."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=partial
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return success_response(
            data=serializer.data,
            message="Course updated successfully"
        )
    
    def destroy(self, request, *args, **kwargs):
        """Soft delete a course (set is_active=False)."""
        instance = self.get_object()
        instance.is_active = False
        instance.save(update_fields=['is_active'])
        
        return success_response(
            message="Course deactivated successfully",
            status_code=status.HTTP_204_NO_CONTENT
        )