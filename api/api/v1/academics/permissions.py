"""
Academics API Permissions - K-12 Focus

Additional permissions specific to academics (beyond core permissions).
"""

from rest_framework import permissions
from apps.academics.models import Enrollment


class IsEnrolledStudent(permissions.BasePermission):
    """
    Permission to check if student is enrolled in the offering.
    """

    def has_object_permission(self, request, view, obj):
        if request.user.role != 'student':
            return False

        # Check if student is enrolled in this offering
        return Enrollment.objects.filter(
            student=request.user,
            offering=obj,
            status='active'
        ).exists()


class IsOfferingTeacher(permissions.BasePermission):
    """
    Permission to check if teacher teaches this offering.
    """

    def has_object_permission(self, request, view, obj):
        if request.user.role != 'teacher':
            return False

        # Check if teacher is assigned to this offering
        return obj.teachers.filter(teacher=request.user).exists()