"""
Academic Structure Views - K-12 Focus

ViewSets for AcademicYear, Term, ClassSection
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.academics.models import (
    AcademicYear,
    Term,
    ClassSection,
)
from ..serializers import (
    AcademicYearSerializer,
    TermListSerializer,
    TermDetailSerializer,
    ClassSectionListSerializer,
    ClassSectionDetailSerializer,
    TermWriteSerializer,
    ClassSectionWriteSerializer,
)
from ..filters import (
    AcademicYearFilter,
    TermFilter,
    ClassSectionFilter,
)
from core.permissions import IsAdminOrDean
from core.responses import success_response, error_response
from core.pagination import StandardResultsSetPagination


class AcademicYearViewSet(viewsets.ModelViewSet):
    """
    ViewSet for AcademicYear.
    
    Permissions:
    - List/Retrieve: All authenticated users
    - Create/Update/Delete: Admin or Dean only
    
    Create action supports both single object and bulk (array) creation.
    """
    
    queryset = AcademicYear.objects.all()
    serializer_class = AcademicYearSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = AcademicYearFilter
    search_fields = ['name']
    ordering_fields = ['start_date', 'created_at']
    ordering = ['-start_date']
    
    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        return [IsAdminOrDean()]
    
    def list(self, request, *args, **kwargs):
        """List all academic years with pagination."""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return success_response(
            data=serializer.data,
            message="Academic years retrieved successfully"
        )
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve a single academic year."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(
            data=serializer.data,
            message="Academic year retrieved successfully"
        )
    
    def create(self, request, *args, **kwargs):
        """
        Create academic year(s).
        
        Supports both:
        - Single object: POST with dict
        - Bulk: POST with list of dicts
        """
        is_many = isinstance(request.data, list)
        
        serializer = self.get_serializer(
            data=request.data,
            many=is_many
        )
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        if is_many:
            message = f"Successfully created {len(serializer.data)} academic year(s)"
        else:
            message = "Academic year created successfully"
        
        return success_response(
            data=serializer.data,
            message=message,
            status_code=status.HTTP_201_CREATED
        )
    
    def perform_create(self, serializer):
        """
        Save academic year(s).
        
        If creating a new current year, unset other current years.
        """
        instances = serializer.save()
        
        # Handle both single and bulk creation
        if not isinstance(instances, list):
            instances = [instances]
        
        if any(instance.is_current for instance in instances):
            AcademicYear.objects.exclude(
                id__in=[instance.id for instance in instances]
            ).update(is_current=False)
    
    def update(self, request, *args, **kwargs):
        """Update an academic year."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return success_response(
            data=serializer.data,
            message="Academic year updated successfully"
        )
    
    def perform_update(self, serializer):
        """Update and handle is_current flag."""
        instance = serializer.save()
        
        if instance.is_current:
            AcademicYear.objects.exclude(id=instance.id).update(is_current=False)
    
    def destroy(self, request, *args, **kwargs):
        """Delete an academic year."""
        instance = self.get_object()
        self.perform_destroy(instance)
        
        return success_response(
            message="Academic year deleted successfully",
            status_code=status.HTTP_204_NO_CONTENT
        )
    
    @action(detail=False, methods=['get'])
    def current(self, request):
        """Get the current academic year."""
        current_year = AcademicYear.objects.filter(is_current=True).first()
        
        if not current_year:
            return error_response(
                message='No current academic year set',
                error_code='NOT_FOUND',
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        serializer = self.get_serializer(current_year)
        return success_response(
            data=serializer.data,
            message="Current academic year retrieved successfully"
        )

class TermViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Term (Grade Levels) - K-12 Focus.

    Permissions:
    - List/Retrieve: All authenticated users
    - Create/Update/Delete: Admin or Dean only
    """

    queryset = Term.objects.select_related('academic_year').all()
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = TermFilter
    search_fields = ['name']
    ordering_fields = ['start_date', 'number']
    ordering = ['-start_date']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return TermListSerializer 
        elif self.action in ['current', 'upcoming']:  
            return TermListSerializer 
        elif self.action in ['create', 'update', 'partial_update']:
            return TermWriteSerializer 
        else:  # retrieve, destroy
            return TermDetailSerializer
    
    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['list', 'retrieve', 'current', 'upcoming']:
            return [IsAuthenticated()]
        return [IsAdminOrDean()]
    
    def list(self, request, *args, **kwargs):
        """List all terms with pagination."""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return success_response(
            data=serializer.data,
            message="Terms retrieved successfully"
        )
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve a single term with nested details."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(
            data=serializer.data,
            message="Term retrieved successfully"
        )
    
    def create(self, request, *args, **kwargs):
        """Create a new term."""
        # Use TermWriteSerializer for validation
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        instance = serializer.instance
        read_serializer = TermDetailSerializer(instance)
        
        return success_response(
            data=read_serializer.data,
            message="Term created successfully",
            status_code=status.HTTP_201_CREATED
        )
    
    def update(self, request, *args, **kwargs):
        """Update a term."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        read_serializer = TermDetailSerializer(instance)
        
        return success_response(
            data=read_serializer.data,
            message="Term updated successfully"
        )
    
    def destroy(self, request, *args, **kwargs):
        """Delete a term."""
        instance = self.get_object()
        self.perform_destroy(instance)
        
        return success_response(
            message="Term deleted successfully",
            status_code=status.HTTP_204_NO_CONTENT
        )
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def current(self, request):
        """Get current terms (within date range)."""
        from django.utils import timezone
        now = timezone.now().date()
        
        terms = self.get_queryset().filter(
            start_date__lte=now,
            end_date__gte=now
        )
        
        serializer = self.get_serializer(terms, many=True)
        return success_response(
            data=serializer.data,
            message="Current terms retrieved successfully"
        )
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def upcoming(self, request):
        """Get upcoming terms."""
        from django.utils import timezone
        now = timezone.now().date()
        
        terms = self.get_queryset().filter(
            start_date__gt=now
        ).order_by('start_date')[:5]
        
        serializer = self.get_serializer(terms, many=True)
        return success_response(
            data=serializer.data,
            message="Upcoming terms retrieved successfully"
        )


class ClassSectionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for ClassSection (K-12 Focus).
    
    Permissions:
    - List/Retrieve: All authenticated users
    - Create/Update/Delete: Admin or Dean only
    
    Serializers:
    - List: ClassSectionListSerializer (minimal, read-only)
    - Retrieve: ClassSectionDetailSerializer (full, read-only)
    - Create/Update: ClassSectionWriteSerializer (accepts FK IDs)
    """
    
    queryset = ClassSection.objects.select_related(
        'term',
        'homeroom_teacher'
    ).all()
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ClassSectionFilter
    search_fields = ['name', 'section']
    ordering_fields = ['name', 'section', 'capacity']
    ordering = ['term__number', 'section']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return ClassSectionListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ClassSectionWriteSerializer
        else:  # retrieve, destroy
            return ClassSectionDetailSerializer
    
    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        return [IsAdminOrDean()]
    
    def list(self, request, *args, **kwargs):
        """List all class sections with pagination."""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return success_response(
            data=serializer.data,
            message="Class sections retrieved successfully"
        )
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve a single class section with full details."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(
            data=serializer.data,
            message="Class section retrieved successfully"
        )
    
    def create(self, request, *args, **kwargs):
        """
        Create a new class section.
        
        Request body:
        {
            "term": 1,
            "section": "A",
            "name": "Grade 5-A",
            "homeroom_teacher": 2,
            "capacity": 30,
            "is_active": true
        }
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        # Return with detail serializer (read-only format)
        instance = serializer.instance
        detail_serializer = ClassSectionDetailSerializer(instance)
        
        return success_response(
            data=detail_serializer.data,
            message="Class section created successfully",
            status_code=status.HTTP_201_CREATED
        )
    
    def update(self, request, *args, **kwargs):
        """Update a class section."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # Return with detail serializer (read-only format)
        detail_serializer = ClassSectionDetailSerializer(instance)
        
        return success_response(
            data=detail_serializer.data,
            message="Class section updated successfully"
        )
    
    def destroy(self, request, *args, **kwargs):
        """Delete a class section."""
        instance = self.get_object()
        self.perform_destroy(instance)
        
        return success_response(
            message="Class section deleted successfully",
            status_code=status.HTTP_204_NO_CONTENT
        )
    
    @action(detail=True, methods=['get'])
    def students(self, request, pk=None):
        """Get all students in this class section."""
        section = self.get_object()
        
        from apps.academics.models import StudentSection
        student_sections = StudentSection.objects.filter(
            class_section=section
        ).select_related('student')
        
        data = [{
            'id': ss.student.id,
            'name': ss.student.name,
            'email': ss.student.email,
            'assigned_at': ss.assigned_at,
        } for ss in student_sections]
        
        return success_response(
            data=data,
            message=f"Students in section '{section.name}' retrieved successfully"
        )
    
    @action(detail=True, methods=['get'])
    def offerings(self, request, pk=None):
        """Get all course offerings for this section."""
        section = self.get_object()
        
        from apps.academics.models import CourseOffering
        offerings = CourseOffering.objects.filter(
            class_section=section,
            is_active=True
        ).select_related('course', 'term')
        
        from ..serializers import CourseOfferingListSerializer
        serializer = CourseOfferingListSerializer(offerings, many=True)
        return success_response(
            data=serializer.data,
            message=f"Course offerings for section '{section.name}' retrieved successfully"
        )
