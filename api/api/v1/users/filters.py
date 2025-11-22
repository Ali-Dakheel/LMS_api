"""
Users API Filters

Django-filter classes for filtering user queryset.
"""

import django_filters
from apps.users.models import User


class UserFilter(django_filters.FilterSet):
    """
    Filter for User model.
    
    Supports filtering by:
    - role (exact match)
    - is_active (boolean)
    - email_verified (boolean)
    - created_at (date range)
    - last_login_at (date range)
    - search (email, name)
    """
    
    role = django_filters.ChoiceFilter(
        choices=User.ROLE_CHOICES,
        help_text="Filter by user role"
    )
    
    is_active = django_filters.BooleanFilter(
        help_text="Filter by active status"
    )
    
    email_verified = django_filters.BooleanFilter(
        help_text="Filter by email verification status"
    )
    
    created_after = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='gte',
        help_text="Filter users created after this date"
    )
    
    created_before = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='lte',
        help_text="Filter users created before this date"
    )
    
    last_login_after = django_filters.DateTimeFilter(
        field_name='last_login_at',
        lookup_expr='gte',
        help_text="Filter users who logged in after this date"
    )
    
    last_login_before = django_filters.DateTimeFilter(
        field_name='last_login_at',
        lookup_expr='lte',
        help_text="Filter users who logged in before this date"
    )

    # Student status filter (K-12 Focus)
    student_status = django_filters.CharFilter(
        field_name='student_info__status',
        lookup_expr='iexact',
        help_text="Filter students by status (active/inactive/graduated/suspended)"
    )

    class Meta:
        model = User
        fields = [
            'role', 'is_active', 'email_verified',
            'created_after', 'created_before',
            'last_login_after', 'last_login_before',
            'student_status'
        ]