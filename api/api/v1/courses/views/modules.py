"""
PathModule and Resource ViewSets
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.utils import timezone

from apps.courses.models import PathModule, Resource, ModuleDetail, ModuleImage
from api.v1.courses.serializers.modules import (
    PathModuleSerializer,
    ResourceSerializer,
    PathModuleListSerializer,
    PathModuleCreateUpdateSerializer,
    ModuleDetailSerializer,
    ModuleImageSerializer,
)
from api.v1.courses.filters import PathModuleFilter
from api.v1.courses.permissions import IsAdminOrReadOnly
from core.responses import success_response, error_response
from core.pagination import StandardResultsSetPagination
from core.permissions import IsAdminOrTeacher
from django.core.exceptions import ObjectDoesNotExist


class PathModuleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for PathModule management.
    
    Permissions:
    - List/Retrieve: All authenticated users
    - Create/Update/Delete: Admin/Teacher only
    """
    
    queryset = PathModule.objects.select_related('path').prefetch_related(
        'resources',
        'images',
        'detail'
    ).all()
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = PathModuleFilter
    search_fields = ['title', 'category']
    ordering_fields = ['order', 'created_at']
    ordering = ['order']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action in ['create', 'update', 'partial_update']:
            return PathModuleCreateUpdateSerializer
        return PathModuleListSerializer

    
    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAdminOrTeacher()]
    
    def list(self, request, *args, **kwargs):
        """List all modules."""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return success_response(
            data=serializer.data,
            message="Modules retrieved successfully"
        )
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve a single module."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(
            data=serializer.data,
            message="Module retrieved successfully"
        )
    
    def create(self, request, *args, **kwargs):
        """Create a new module."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        return success_response(
            data=serializer.data,
            message="Module created successfully",
            status_code=status.HTTP_201_CREATED
        )
    
    def update(self, request, *args, **kwargs):
        """Update a module."""
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
            message="Module updated successfully"
        )
    
    def destroy(self, request, *args, **kwargs):
        """Delete a module."""
        instance = self.get_object()
        self.perform_destroy(instance)
        
        return success_response(
            message="Module deleted successfully",
            status_code=status.HTTP_204_NO_CONTENT
        )
    
    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        """Publish a module."""
        module = self.get_object()
        
        # Check if detail exists
        try:
            has_detail = module.detail is not None
        except ObjectDoesNotExist:
            has_detail = False
        
        if not has_detail:
            return error_response(
                message="Cannot publish module: Module detail content is required",
                error_code="MISSING_MODULE_DETAIL",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        module.is_published = True
        module.published_at = timezone.now()
        module.save()
        
        serializer = self.get_serializer(module)
        return success_response(
            data=serializer.data,
            message="Module published successfully"
        )


class ResourceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Resource management.
    
    Permissions:
    - List/Retrieve: All authenticated users
    - Create/Update/Delete: Admin/Teacher only
    """
    
    queryset = Resource.objects.select_related('module').all()
    pagination_class = StandardResultsSetPagination
    serializer_class = ResourceSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['order', 'created_at']
    ordering = ['order']
    
    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAdminOrTeacher()]
    
    def list(self, request, *args, **kwargs):
        """List all resources."""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return success_response(
            data=serializer.data,
            message="Resources retrieved successfully"
        )
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve a single resource."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(
            data=serializer.data,
            message="Resource retrieved successfully"
        )
    
    def create(self, request, *args, **kwargs):
        """Create a new resource."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        return success_response(
            data=serializer.data,
            message="Resource created successfully",
            status_code=status.HTTP_201_CREATED
        )
    
    def update(self, request, *args, **kwargs):
        """Update a resource."""
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
            message="Resource updated successfully"
        )
    
    def destroy(self, request, *args, **kwargs):
        """Delete a resource."""
        instance = self.get_object()
        self.perform_destroy(instance)
        
        return success_response(
            message="Resource deleted successfully",
            status_code=status.HTTP_204_NO_CONTENT
        )
    
class ModuleDetailViewSet(viewsets.ModelViewSet):
    """
    ViewSet for ModuleDetail management.
    
    Each module can have one detail (OneToOne relationship).
    
    Permissions:
    - List/Retrieve: All authenticated users
    - Create/Update/Delete: Admin/Teacher only
    """
    
    queryset = ModuleDetail.objects.select_related('module').all()
    serializer_class = ModuleDetailSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['module__title', 'objectives']
    ordering_fields = ['created_at', 'is_ai_generated']
    ordering = ['-created_at']
    
    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAdminOrTeacher()]
    
    def list(self, request, *args, **kwargs):
        """List all module details."""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return success_response(
            data=serializer.data,
            message="Module details retrieved successfully"
        )
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve a single module detail."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(
            data=serializer.data,
            message="Module detail retrieved successfully"
        )
    
    def create(self, request, *args, **kwargs):
        """Create module detail."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Check if module already has a detail (OneToOne)
        module_id = request.data.get('module')
        if ModuleDetail.objects.filter(module_id=module_id).exists():
            return error_response(
                message="This module already has a detail. Update it instead.",
                error_code="ALREADY_EXISTS",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        self.perform_create(serializer)
        
        return success_response(
            data=serializer.data,
            message="Module detail created successfully",
            status_code=status.HTTP_201_CREATED
        )
    
    def update(self, request, *args, **kwargs):
        """Update module detail."""
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
            message="Module detail updated successfully"
        )
    
    def destroy(self, request, *args, **kwargs):
        """Delete module detail."""
        instance = self.get_object()
        self.perform_destroy(instance)
        
        return success_response(
            message="Module detail deleted successfully",
            status_code=status.HTTP_204_NO_CONTENT
        )


class ModuleImageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for ModuleImage management.
    
    Permissions:
    - List/Retrieve: All authenticated users
    - Create/Update/Delete: Admin/Teacher only
    """
    
    queryset = ModuleImage.objects.select_related('module').all()
    serializer_class = ModuleImageSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['module__title', 'title']
    ordering_fields = ['order', 'created_at']
    ordering = ['order']
    
    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAdminOrTeacher()]
    
    def list(self, request, *args, **kwargs):
        """List all module images."""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return success_response(
            data=serializer.data,
            message="Module images retrieved successfully"
        )
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve a single module image."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(
            data=serializer.data,
            message="Module image retrieved successfully"
        )
    
    def create(self, request, *args, **kwargs):
        """Create module image."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        return success_response(
            data=serializer.data,
            message="Module image created successfully",
            status_code=status.HTTP_201_CREATED
        )
    
    def update(self, request, *args, **kwargs):
        """Update module image."""
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
            message="Module image updated successfully"
        )
    
    def destroy(self, request, *args, **kwargs):
        """Delete module image."""
        instance = self.get_object()
        self.perform_destroy(instance)
        
        return success_response(
            message="Module image deleted successfully",
            status_code=status.HTTP_204_NO_CONTENT
        )
