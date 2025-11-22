"""
Courses App Models
"""

from .subject import Subject
from .course import Course
from .path import CoursePath
from .module import PathModule, ModulePackage, ModuleDetail, ModuleImage
from .resource import Resource, ModuleToolOverride

from .managers import (
    SubjectManager,
    CourseManager,
    CoursePathManager,
    PathModuleManager,
    ResourceManager,
    ModulePackageManager,
)

__all__ = [
    'Subject',
    'Course',
    'CoursePath',
    'PathModule',
    'ModulePackage',
    'ModuleDetail',
    'ModuleImage',
    'Resource',
    'ModuleToolOverride',
    # Managers
    'SubjectManager',
    'CourseManager',
    'CoursePathManager',
    'PathModuleManager',
    'ResourceManager',
    'ModulePackageManager',
]