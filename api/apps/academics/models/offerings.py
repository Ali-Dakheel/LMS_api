"""
Course Offering Models

Course delivery and scheduling:
- CourseOffering: Specific course instance for a section/term
- OfferingTeacher: Teacher assignments to offerings
- ClassSession: Individual class meetings
"""

from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.contrib.auth import get_user_model

from .structure import Term, ClassSection
from .managers import CourseOfferingManager, OfferingTeacherManager

User = get_user_model()


class CourseOffering(models.Model):
    """
    Represents a specific course taught in a specific term to a specific section.
    
    Example:
    - Course: "English 101"
    - Term: "Fall 2024"
    - Section: "Grade 5-A" or "CS-2024-A"
    - Result: "English 101 for Grade 5-A in Fall 2024"
    
    Business Rules:
    - Unique per course, term, and section
    - Auto-enrollment based on strategy
    - Has generation status for AI content
    - Can override section capacity
    
    Use Cases:
    - Course scheduling
    - Student enrollment
    - Content generation tracking
    - Teacher assignment
    """
    
    objects = CourseOfferingManager()
    
    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.CASCADE,
        related_name='offerings',
        db_index=True
    )
    term = models.ForeignKey(
        Term,
        on_delete=models.CASCADE,
        related_name='course_offerings',
        db_index=True
    )
    class_section = models.ForeignKey(
        ClassSection,
        on_delete=models.CASCADE,
        related_name='course_offerings',
        db_index=True
    )
    
    slug = models.SlugField(
        unique=True,
        max_length=255,
        db_index=True,
        help_text="Auto-generated URL slug"
    )
    
    AUTO_ENROLLMENT_CHOICES = [
        ('none', 'Manual enrollment only'),
        ('section', 'Auto-enroll section students (K-12)'),
    ]
    auto_enroll = models.CharField(
        max_length=10,
        choices=AUTO_ENROLLMENT_CHOICES,
        default='section',
        help_text="Automatic enrollment strategy for K-12"
    )
    
    capacity = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Max students (overrides section capacity if set)"
    )
    
    GENERATION_STATUS_CHOICES = [
        ('not_generated', 'Not Generated'),
        ('partial', 'Partial'),
        ('complete', 'Complete'),
    ]
    generation_status = models.CharField(
        max_length=20,
        choices=GENERATION_STATUS_CHOICES,
        default='not_generated',
        db_index=True,
        help_text="AI content generation status"
    )
    
    is_active = models.BooleanField(
        default=True,
        db_index=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'course_offerings'
        verbose_name = 'Course Offering'
        verbose_name_plural = 'Course Offerings'
        unique_together = ['course', 'term', 'class_section']
        ordering = ['-term__start_date', 'course__title']
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['generation_status']),
            models.Index(fields=['course', 'term']),
            models.Index(fields=['slug']),
        ]
    
    def __str__(self):
        return f"{self.course.title} - {self.class_section.name} ({self.term.name})"
    
    def save(self, *args, **kwargs):
        """Auto-generate slug if not provided."""
        if not self.slug:
            slug_base = f"{self.course.slug}-t{self.term.id}-s{self.class_section.id}"
            self.slug = slugify(slug_base)
        
        super().save(*args, **kwargs)
    
    @property
    def effective_capacity(self):
        """Get effective capacity (offering or section)."""
        return self.capacity or self.class_section.capacity
    
    @property
    def enrollment_count(self):
        """Get current active enrollment count."""
        return self.enrollments.filter(status='active').count()
    
    @property
    def is_full(self):
        """Check if offering is at capacity."""
        return self.enrollment_count >= self.effective_capacity
    
    @property
    def available_seats(self):
        """Get number of available seats."""
        return max(0, self.effective_capacity - self.enrollment_count)


class OfferingTeacher(models.Model):
    """
    Explicit many-to-many between CourseOffering and Teacher.
    
    Allows:
    - Multiple teachers per offering (co-teaching)
    - Primary teacher designation
    - Teacher-specific tracking
    - Assignment history
    
    Business Rules:
    - Only one primary teacher per offering
    - Teacher must have role='teacher'
    - Unique per offering and teacher
    """
    
    objects = OfferingTeacherManager()
    
    offering = models.ForeignKey(
        CourseOffering,
        on_delete=models.CASCADE,
        related_name='teachers',
        db_index=True
    )
    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='taught_offerings',
        limit_choices_to={'role': 'teacher'},
        db_index=True
    )
    
    is_primary = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Primary teacher for grading/reporting"
    )
    
    assigned_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'offering_teachers'
        verbose_name = 'Offering Teacher'
        verbose_name_plural = 'Offering Teachers'
        unique_together = ['offering', 'teacher']
        ordering = ['-is_primary', 'assigned_at']
        indexes = [
            models.Index(fields=['offering', 'is_primary']),
            models.Index(fields=['teacher']),
        ]
    
    def __str__(self):
        primary = "(Primary)" if self.is_primary else ""
        return f"{self.teacher.name} → {self.offering} {primary}"
    
    def save(self, *args, **kwargs):
        """Ensure only one primary teacher per offering."""
        if self.is_primary:
            # Set all other teachers to non-primary
            OfferingTeacher.objects.filter(
                offering=self.offering,
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        
        super().save(*args, **kwargs)


class ClassSession(models.Model):
    """
    Represents individual class meetings for attendance tracking.
    
    Example:
    - "English 101 for Grade 5-A" has sessions on:
      - 2024-09-05 09:00-10:30 (Monday)
      - 2024-09-07 09:00-10:30 (Wednesday)
      - 2024-09-12 09:00-10:30 (Monday)
    
    Use Cases:
    - Per-session attendance tracking
    - Class scheduling
    - Session-specific content
    - Detailed analytics
    
    Business Rules:
    - Must be within term dates
    - End time after start time
    - Can be cancelled
    """
    
    offering = models.ForeignKey(
        CourseOffering,
        on_delete=models.CASCADE,
        related_name='class_sessions',
        db_index=True
    )
    
    session_date = models.DateField(
        db_index=True,
        help_text="Date of class session"
    )
    start_time = models.TimeField(
        help_text="Class start time"
    )
    end_time = models.TimeField(
        help_text="Class end time"
    )
    
    topic = models.CharField(
        max_length=255,
        blank=True,
        help_text="Topic covered in this session"
    )
    notes = models.TextField(
        blank=True,
        help_text="Additional session notes"
    )
    
    is_cancelled = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Mark session as cancelled"
    )
    cancellation_reason = models.TextField(
        blank=True,
        help_text="Reason for cancellation"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'class_sessions'
        verbose_name = 'Class Session'
        verbose_name_plural = 'Class Sessions'
        ordering = ['-session_date', '-start_time']
        indexes = [
            models.Index(fields=['offering', 'session_date']),
            models.Index(fields=['is_cancelled']),
            models.Index(fields=['session_date']),
        ]
    
    def __str__(self):
        status = " (Cancelled)" if self.is_cancelled else ""
        return f"{self.offering.course.title} - {self.session_date} {self.start_time}{status}"
    
    def clean(self):
        """Validate class session times and dates."""
        errors = {}
        
        # Validate times
        if self.start_time and self.end_time:
            if self.start_time >= self.end_time:
                errors['end_time'] = _('End time must be after start time')
        
        # Validate session date is within term
        if self.offering_id and self.session_date:
            term = self.offering.term
            if not (term.start_date <= self.session_date <= term.end_date):
                errors['session_date'] = _(
                    f'Session date must be within term dates '
                    f'({term.start_date} to {term.end_date})'
                )
        
        if errors:
            raise ValidationError(errors)
    
    @property
    def duration_minutes(self):
        """Calculate session duration in minutes."""
        from datetime import datetime, timedelta
        start = datetime.combine(datetime.today(), self.start_time)
        end = datetime.combine(datetime.today(), self.end_time)
        duration = end - start
        return int(duration.total_seconds() / 60)
    
    @property
    def attendance_count(self):
        """Get number of attendance records."""
        return self.attendance_records.count()
    
    @property
    def present_count(self):
        """Get number of students marked present."""
        return self.attendance_records.filter(status='present').count()


class Attendance(models.Model):
    """
    Tracks student attendance for individual class sessions.
    
    Business Rules:
    - Unique per student and session
    - Status must be valid choice
    - Can include notes for absences
    """
    
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('excused', 'Excused'),
    ]
    
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='attendance_records',
        limit_choices_to={'role': 'student'},
        db_index=True
    )
    class_session = models.ForeignKey(
        ClassSession,
        on_delete=models.CASCADE,
        related_name='attendance_records',
        db_index=True
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        db_index=True
    )
    notes = models.TextField(
        blank=True,
        help_text="Additional notes about absence/lateness"
    )
    
    marked_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='marked_attendance',
        limit_choices_to={'role__in': ['teacher', 'admin']},
        help_text="Who marked the attendance"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'attendance'
        verbose_name = 'Attendance Record'
        verbose_name_plural = 'Attendance Records'
        unique_together = ['student', 'class_session']
        ordering = ['-class_session__session_date']
        indexes = [
            models.Index(fields=['student', 'status']),
            models.Index(fields=['class_session', 'status']),
        ]
    
    def __str__(self):
        return f"{self.student.name} - {self.class_session} ({self.status})"