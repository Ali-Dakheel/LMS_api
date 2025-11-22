"""
Courses App Permissions

Uses core.permissions classes for consistency.
"""

from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdminOrReadOnly(BasePermission):
    """
    Allow admins to create/edit.
    Allow all to read published content.
    """
    
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated and request.user.role == 'admin'


class IsOwnerOrAdmin(BasePermission):
    """
    Allow owner or admin to edit objects.
    Useful for teacher/student-owned content.
    """
    
    def has_object_permission(self, request, view, obj):
        # Admin can do anything
        if request.user and request.user.role == 'admin':
            return True
        
        # Check if user is owner (for teacher/student paths)
        if hasattr(obj, 'teacher') and obj.teacher == request.user:
            return True
        if hasattr(obj, 'student') and obj.student == request.user:
            return True
        
        return False