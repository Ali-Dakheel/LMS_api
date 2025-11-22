from .subjects import SubjectViewSet
from .courses import CourseViewSet
from .paths import CoursePathViewSet
from .modules import PathModuleViewSet, ResourceViewSet, ModuleDetailViewSet, ModuleImageViewSet

__all__ = [
    'SubjectViewSet',
    'CourseViewSet',
    'CoursePathViewSet',
    'PathModuleViewSet',
    'ResourceViewSet',
    'ModuleDetailViewSet',
    'ModuleImageViewSet',
]