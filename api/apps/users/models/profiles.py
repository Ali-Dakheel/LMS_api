"""
User Profile Models - Role-specific information

Models:
- TeacherInfo: For teachers and deans
- StudentInfo: For students
- PasswordHistory: Security tracking
"""

from django.db import models


class TeacherInfo(models.Model):
    """
    Extended information for teachers and deans (K-12).

    Tracks:
    - Professional designation
    - Subject specialization
    - Denormalized counts (courses, subjects)
    """

    user = models.OneToOneField(
        'users.User',
        on_delete=models.CASCADE,
        related_name='teacher_info',
        primary_key=True
    )
    designation = models.CharField(
        max_length=255,
        blank=True,
        help_text="e.g., Senior Teacher, Lead Teacher, Department Head, Dean"
    )
    specialization = models.CharField(
        max_length=255,
        blank=True,
        help_text="e.g., Mathematics, Physics, Computer Science"
    )

    # Denormalized counters (updated via signals)
    courses_count = models.PositiveIntegerField(
        default=0,
        db_index=True,
        help_text="Number of active course offerings"
    )
    subjects_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of assigned subjects"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'teachers'
        verbose_name_plural = 'Teacher Info'
        indexes = [
            models.Index(fields=['courses_count']),
        ]

    def __str__(self):
        spec = self.specialization or 'Unspecified'
        return f"Teacher: {self.user.name} ({spec})"


class StudentInfo(models.Model):
    """
    Extended information for K-12 students.

    Tracks:
    - Enrollment status
    - Enrollment number (roll number)
    - Class section (homeroom)
    - Denormalized course count
    """

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('graduated', 'Graduated'),
        ('suspended', 'Suspended'),
    ]

    user = models.OneToOneField(
        'users.User',
        on_delete=models.CASCADE,
        related_name='student_info',
        primary_key=True
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        db_index=True,
        help_text="Current enrollment status"
    )
    enrollment_number = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        help_text="Unique student ID/roll number"
    )

    # Academic assignment (K-12 homeroom)
    class_section = models.ForeignKey(
        'academics.ClassSection',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='student_infos',
        help_text="Assigned class section (K-12 homeroom)"
    )

    # Denormalized counter (updated via signals)
    enrolled_courses_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of active enrollments"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'students'
        verbose_name_plural = 'Student Info'
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['enrollment_number']),
            models.Index(fields=['class_section']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(status__in=['active', 'inactive', 'graduated', 'suspended']),
                name='valid_student_status'
            )
        ]

    def __str__(self):
        enrollment = self.enrollment_number or 'N/A'
        return f"Student: {self.user.name} ({enrollment})"


class PasswordHistory(models.Model):
    """Password history for security compliance."""
    
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='password_history'
    )
    hashed_password = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'password_history'
        verbose_name_plural = 'Password History'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]
    
    def check_password(self, raw_password):
        """
        Check if raw password matches this historical password.
        
        Args:
            raw_password: Plain-text password to check
        
        Returns:
            bool: True if passwords match
        """
        from django.contrib.auth.hashers import check_password
        return check_password(raw_password, self.hashed_password)
    
    def __str__(self):
        return f"Password history for {self.user.email} at {self.created_at}"