"""
User Manager - Custom query methods for User model

Provides:
- Custom user creation (create_user, create_superuser)
- Role-based query methods with optimization
- Query optimization with select_related/prefetch_related
"""

from django.contrib.auth.models import BaseUserManager


class UserManager(BaseUserManager):
    """Custom manager for User model with email-based authentication."""
    
    def create_user(self, email, password=None, **extra_fields):
        """
        Create and save a regular user.
        
        Args:
            email: User's email address (normalized)
            password: Plain-text password (will be hashed)
            **extra_fields: Additional user fields (name, role, etc)
        
        Returns:
            User: Created user instance
        
        Raises:
            ValueError: If email is not provided
        """
        if not email:
            raise ValueError('Email is required')
        
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        
        # Note: Profile auto-creation happens via signal (profile_signals.py)
        # No need to create here - signals handle it
        
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """
        Create and save a superuser with admin role.
        
        Args:
            email: Admin email address
            password: Admin password
            **extra_fields: Additional fields
        
        Returns:
            User: Created admin user
        
        Raises:
            ValueError: If is_staff or is_superuser is not True
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')
        extra_fields.setdefault('name', email.split('@')[0])
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True')
        
        return self.create_user(email, password, **extra_fields)
    
    # ============================================================================
    # ROLE-BASED QUERY METHODS (DRY - use get_by_role internally)
    # ============================================================================
    
    def get_by_role(self, role):
        """
        Get active users by role with optimal prefetching.

        Automatically selects related objects based on role:
        - Teachers/Deans: Prefetch teacher_info
        - Students: Prefetch student_info and class_section

        Args:
            role: User role (admin, dean, teacher, student)

        Returns:
            QuerySet: Optimized queryset for the role
        """
        queryset = self.filter(role=role, is_active=True)

        if role in ['teacher', 'dean']:
            queryset = queryset.select_related('teacher_info')
        elif role == 'student':
            queryset = queryset.select_related(
                'student_info',
                'student_info__class_section'
            )

        return queryset
    
    def get_teachers(self):
        """
        Get all active teachers with optimized query.
        
        Returns:
            QuerySet: Active teacher users
        """
        return self.get_by_role('teacher')
    
    def get_students(self):
        """
        Get all active students with optimized query.
        
        Returns:
            QuerySet: Active student users
        """
        return self.get_by_role('student')
    
    def get_deans(self):
        """
        Get all active deans with optimized query.
        
        Returns:
            QuerySet: Active dean users
        """
        return self.get_by_role('dean')
    
    def get_admins(self):
        """
        Get all active admins with optimized query.
        
        Returns:
            QuerySet: Active admin users
        """
        return self.filter(role='admin', is_active=True)