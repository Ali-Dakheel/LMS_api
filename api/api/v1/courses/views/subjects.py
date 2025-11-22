"""
Subject ViewSet
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.courses.models import Subject
from api.v1.courses.serializers.subjects import (
    SubjectListSerializer,
    SubjectDetailSerializer,
)
from api.v1.courses.filters import SubjectFilter
from api.v1.courses.permissions import IsAdminOrReadOnly
from core.responses import success_response
from core.pagination import StandardResultsSetPagination


class SubjectViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Subject management.
    
    Permissions:
    - List/Retrieve: All authenticated users
    - Create/Update/Delete: Admin only
    """
    
    queryset = Subject.objects.all()
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = SubjectFilter
    search_fields = ['name', 'code']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return SubjectListSerializer
        return SubjectDetailSerializer
    
    def list(self, request, *args, **kwargs):
        """List all subjects with pagination."""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return success_response(
            data=serializer.data,
            message="Subjects retrieved successfully"
        )
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve a single subject."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(
            data=serializer.data,
            message="Subject retrieved successfully"
        )
    
    def create(self, request, *args, **kwargs):
        """Create a new subject."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        return success_response(
            data=serializer.data,
            message="Subject created successfully",
            status_code=status.HTTP_201_CREATED
        )
    
    def update(self, request, *args, **kwargs):
        """Update a subject."""
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
            message="Subject updated successfully"
        )
    
    def destroy(self, request, *args, **kwargs):
        """Delete a subject."""
        instance = self.get_object()
        self.perform_destroy(instance)
        
        return success_response(
            message="Subject deleted successfully",
            status_code=status.HTTP_204_NO_CONTENT
        )
    
    @action(detail=False, methods=['get'])
    def active_only(self, request):
        """Get only active subjects."""
        queryset = self.filter_queryset(
            self.get_queryset().filter(is_active=True)
        )
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return success_response(
            data=serializer.data,
            message="Active subjects retrieved successfully"
        )