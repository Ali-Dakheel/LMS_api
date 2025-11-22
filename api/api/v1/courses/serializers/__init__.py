from .subjects import SubjectListSerializer, SubjectDetailSerializer
from .courses import CourseListSerializer, CourseDetailSerializer
from .paths import CoursePathListSerializer, CoursePathDetailSerializer
from .modules import (
    PathModuleSerializer,
    ModuleDetailSerializer,
    ModuleImageSerializer,
    ResourceSerializer,
)

__all__ = [
    'SubjectListSerializer',
    'SubjectDetailSerializer',
    'CourseListSerializer',
    'CourseDetailSerializer',
    'CoursePathListSerializer',
    'CoursePathDetailSerializer',
    'PathModuleSerializer',
    'ModuleDetailSerializer',
    'ModuleImageSerializer',
    'ResourceSerializer',
]