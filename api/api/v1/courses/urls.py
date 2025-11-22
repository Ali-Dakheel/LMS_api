"""
Courses API URL Configuration
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    SubjectViewSet,
    CourseViewSet,
    CoursePathViewSet,
    PathModuleViewSet,
    ModuleDetailViewSet,
    ModuleImageViewSet,
    ResourceViewSet,
)

router = DefaultRouter()
router.register(r'subjects', SubjectViewSet, basename='subject')
router.register(r'courses', CourseViewSet, basename='course')
router.register(r'paths', CoursePathViewSet, basename='coursepath')
router.register(r'modules', PathModuleViewSet, basename='pathmodule')
router.register(r'module-details', ModuleDetailViewSet, basename='moduledetail')  
router.register(r'module-images', ModuleImageViewSet, basename='moduleimage')     
router.register(r'resources', ResourceViewSet, basename='resource')

urlpatterns = [
    path('', include(router.urls)),
]