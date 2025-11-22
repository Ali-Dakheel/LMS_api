"""
Enrollment Models

Student course enrollment:
- Enrollment: Student enrollment in course offerings
- EnrollmentWaitlist: Waitlist for full courses
- StudentEligibility: Prerequisite checking
"""

from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

from .offerings import CourseOffering
from .managers import EnrollmentManager

User = get_user_model()


class Enrollment(models.Model):
    """
    Represents a student's enrollment in a course offering.
    
    Tracks:
    - Which student
    - Which course offering
    - Enrollment status (active, dropped, completed, failed)
    - Important dates (enrolled, dropped, completed)
    
    Business Rules:
    - Unique per student and offering
    - Capacity validation on creation
    - Status transitions tracked
    - Atomic enrollment with capacity check
    """
    
    objects = EnrollmentManager()
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),      # Awaiting approval
        ('active', 'Active'),        # Currently enrolled
        ('dropped', 'Dropped'),      # Student dropped
        ('completed', 'Completed'),  # Course completed
        ('failed', 'Failed'),        # Failed course
    ]
    
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='enrollments',
        limit_choices_to={'role': 'student'},
        db_index=True
    )
    offering = models.ForeignKey(
        CourseOffering,
        on_delete=models.CASCADE,
        related_name='enrollments',
        db_index=True
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        db_index=True
    )
    
    enrolled_at = models.DateTimeField(auto_now_add=True)
    dropped_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When student dropped the course"
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When course was completed"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'enrollments'
        verbose_name = 'Enrollment'
        verbose_name_plural = 'Enrollments'
        unique_together = ['student', 'offering']
        ordering = ['-enrolled_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['student', 'status']),
            models.Index(fields=['offering', 'status']),
        ]
    
    def __str__(self):
        return f"{self.student.name} → {self.offering.course.title} ({self.status})"
    
    def save(self, *args, **kwargs):
        """
        Save with capacity validation.
        
        Uses atomic transaction with select_for_update to prevent
        race conditions in concurrent enrollments.
        """
        if self.status == 'active' and self.pk is None:  # New active enrollment
            with transaction.atomic():
                # Lock the offering row to prevent race conditions
                offering = CourseOffering.objects.select_for_update().get(
                    pk=self.offering_id
                )
                
                # Count active enrollments
                active_count = Enrollment.objects.filter(
                    offering=offering,
                    status__in=['active', 'pending']
                ).count()
                
                capacity = offering.effective_capacity
                
                if active_count >= capacity:
                    raise ValidationError(
                        _('Course offering is at capacity. Please join waitlist instead.'),
                        code='capacity_exceeded'
                    )
                
                self.full_clean()
                super().save(*args, **kwargs)
        else:
            self.full_clean()
            super().save(*args, **kwargs)
    
    def drop(self, reason=''):
        """
        Drop enrollment.
        
        Updates status and sets dropped_at timestamp.
        """
        from django.utils import timezone
        
        if self.status not in ['active', 'pending']:
            raise ValidationError(
                _('Can only drop active or pending enrollments'),
                code='invalid_status'
            )
        
        self.status = 'dropped'
        self.dropped_at = timezone.now()
        self.save(update_fields=['status', 'dropped_at', 'updated_at'])
    
    def complete(self, passed=True):
        """
        Mark enrollment as completed or failed.
        
        Args:
            passed: True if student passed, False if failed
        """
        from django.utils import timezone
        
        if self.status != 'active':
            raise ValidationError(
                _('Can only complete active enrollments'),
                code='invalid_status'
            )
        
        self.status = 'completed' if passed else 'failed'
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'completed_at', 'updated_at'])


class EnrollmentWaitlist(models.Model):
    """
    Tracks students waiting to enroll when capacity becomes available.
    
    Use Cases:
    - Popular courses that fill up quickly
    - Priority-based enrollment
    - Automatic enrollment when space opens
    
    Business Rules:
    - Position determines priority
    - Lower position number = higher priority
    - Auto-advanced when enrollment drops
    """
    
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='enrollment_waitlist',
        limit_choices_to={'role': 'student'},
        db_index=True
    )
    offering = models.ForeignKey(
        CourseOffering,
        on_delete=models.CASCADE,
        related_name='waitlist',
        db_index=True
    )
    
    position = models.PositiveIntegerField(
        db_index=True,
        help_text="Position in waitlist (1 = first in line)"
    )
    
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'enrollment_waitlist'
        verbose_name = 'Enrollment Waitlist'
        verbose_name_plural = 'Enrollment Waitlist'
        unique_together = ['student', 'offering']
        ordering = ['position']
        indexes = [
            models.Index(fields=['offering', 'position']),
        ]
    
    def __str__(self):
        return f"{self.student.name} - {self.offering.course.title} (#{self.position})"
    
    def save(self, *args, **kwargs):
        """Auto-assign position if not provided."""
        if self.position is None or self.position == 0:
            # Get max position for this offering
            max_pos = EnrollmentWaitlist.objects.filter(
                offering=self.offering
            ).aggregate(models.Max('position'))['position__max'] or 0
            
            self.position = max_pos + 1
        
        super().save(*args, **kwargs)


class StudentEligibility(models.Model):
    """
    Tracks student eligibility to enroll in courses.
    
    Use Cases:
    - Prerequisite validation
    - GPA requirements
    - Academic standing
    - Manual eligibility overrides
    
    Example:
    - Student "Alice" is eligible for CS 300-level (met prerequisites)
    - Student "Bob" is NOT eligible (low GPA)
    - Admin can manually override for special cases
    """
    
    STATUS_CHOICES = [
        ('eligible', 'Eligible'),
        ('not_eligible', 'Not Eligible'),
        ('override', 'Override (Eligible)'),
        ('pending_review', 'Pending Review'),
    ]
    
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='eligibilities',
        limit_choices_to={'role': 'student'},
        db_index=True
    )
    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.CASCADE,
        related_name='student_eligibilities',
        db_index=True
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending_review',
        db_index=True
    )
    reason = models.TextField(
        blank=True,
        help_text="Why student is/isn't eligible"
    )
    
    # Manual override tracking
    overridden_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='eligibility_overrides',
        limit_choices_to={'role__in': ['admin', 'dean']},
        help_text="Admin/Dean who overrode eligibility"
    )
    overridden_at = models.DateTimeField(
        null=True,
        blank=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'student_eligibilities'
        verbose_name = 'Student Eligibility'
        verbose_name_plural = 'Student Eligibilities'
        unique_together = ['student', 'course']
        ordering = ['status', '-created_at']
        indexes = [
            models.Index(fields=['student', 'status']),
            models.Index(fields=['course', 'status']),
        ]
    
    def __str__(self):
        return f"{self.student.name} → {self.course.title} ({self.status})"
    
    def override(self, admin_user, reason=''):
        """
        Manually override eligibility.
        
        Args:
            admin_user: Admin/Dean performing override
            reason: Reason for override
        """
        from django.utils import timezone
        
        if admin_user.role not in ['admin', 'dean']:
            raise ValidationError(
                _('Only admins and deans can override eligibility'),
                code='permission_denied'
            )
        
        self.status = 'override'
        self.reason = reason
        self.overridden_by = admin_user
        self.overridden_at = timezone.now()
        self.save()