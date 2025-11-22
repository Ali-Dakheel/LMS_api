"""
Courses App Managers

All QuerySet and Manager classes for courses models.
"""

from django.db import models
from django.db.models import Prefetch, Q, F, Count


# ============================================================================
# SUBJECT MANAGER
# ============================================================================

class SubjectQuerySet(models.QuerySet):
    """QuerySet for Subject."""
    
    def active_only(self):
        return self.filter(is_active=True)
    
    def by_level(self, level):
        return self.filter(level=level)
    
    def with_courses(self):
        return self.prefetch_related('courses')


class SubjectManager(models.Manager):
    def get_queryset(self):
        return SubjectQuerySet(self.model, using=self._db)
    
    def active_only(self):
        return self.get_queryset().active_only()
    
    def by_level(self, level):
        return self.get_queryset().by_level(level)


# ============================================================================
# COURSE MANAGER
# ============================================================================

class CourseQuerySet(models.QuerySet):
    """QuerySet for Course."""
    
    def with_subject(self):
        return self.select_related('subject')
    
    def active_only(self):
        return self.filter(is_active=True)
    
    def by_level(self, level):
        return self.filter(level=level)
    
    def with_paths(self):
        return self.prefetch_related('paths')
    
    def analyzed(self):
        return self.filter(syllabus_analysis_status='analyzed')


class CourseManager(models.Manager):
    def get_queryset(self):
        return CourseQuerySet(self.model, using=self._db)
    
    def with_subject(self):
        return self.get_queryset().with_subject()
    
    def active_only(self):
        return self.get_queryset().active_only()


# ============================================================================
# COURSE PATH MANAGER
# ============================================================================

class CoursePathQuerySet(models.QuerySet):
    """QuerySet for CoursePath with scope-aware queries."""
    
    def with_modules(self):
        from apps.courses.models import PathModule
        modules_prefetch = Prefetch(
            'modules',
            PathModule.objects.prefetch_related('resources', 'images')
        )
        return self.prefetch_related(modules_prefetch)
    
    def with_course(self):
        return self.select_related('course', 'course__subject')
    
    def with_all_relations(self):
        return self.select_related(
            'course', 'course__subject', 'teacher', 'student',
            'offering', 'offering__course', 'offering__term', 'source_book',
        ).with_modules()
    
    def published_only(self):
        return self.filter(is_published=True)
    
    def for_course(self, course):
        return self.filter(course=course)
    
    def for_scope(self, scope):
        return self.filter(scope=scope)
    
    def for_teacher(self, teacher):
        return self.filter(
            Q(scope='course', course__offerings__teachers__teacher=teacher) |
            Q(scope='teacher', teacher=teacher)
        ).distinct()
    
    def for_student(self, student):
        return self.filter(
            Q(scope='course', course__offerings__enrollments__student=student) |
            Q(scope='student', student=student) |
            Q(scope='offering', offering__enrollments__student=student)
        ).distinct()


class CoursePathManager(models.Manager):
    def get_queryset(self):
        return CoursePathQuerySet(self.model, using=self._db)
    
    def with_modules(self):
        return self.get_queryset().with_modules()
    
    def published_only(self):
        return self.get_queryset().published_only()
    
    def for_teacher(self, teacher):
        return self.get_queryset().for_teacher(teacher)
    
    def for_student(self, student):
        return self.get_queryset().for_student(student)


# ============================================================================
# PATH MODULE MANAGER
# ============================================================================

class PathModuleQuerySet(models.QuerySet):
    def with_resources(self):
        return self.prefetch_related('resources', 'images')
    
    def with_path(self):
        return self.select_related('path', 'path__course')
    
    def published_only(self):
        return self.filter(is_published=True)
    
    def by_category(self, category):
        return self.filter(category=category)


class PathModuleManager(models.Manager):
    def get_queryset(self):
        return PathModuleQuerySet(self.model, using=self._db)
    
    def published_only(self):
        return self.get_queryset().published_only()


# ============================================================================
# RESOURCE MANAGER
# ============================================================================

class ResourceQuerySet(models.QuerySet):
    def by_type(self, resource_type):
        return self.filter(type=resource_type)
    
    def required_only(self):
        return self.filter(is_required=True)
    
    def with_module(self):
        return self.select_related('module', 'module__path')


class ResourceManager(models.Manager):
    def get_queryset(self):
        return ResourceQuerySet(self.model, using=self._db)
    
    def by_type(self, resource_type):
        return self.get_queryset().by_type(resource_type)


# ============================================================================
# MODULE PACKAGE MANAGER
# ============================================================================

class ModulePackageQuerySet(models.QuerySet):
    def with_module(self):
        return self.select_related('module', 'module__path')


class ModulePackageManager(models.Manager):
    def get_queryset(self):
        return ModulePackageQuerySet(self.model, using=self._db)