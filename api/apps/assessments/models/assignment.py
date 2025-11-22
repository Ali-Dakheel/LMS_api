"""
Assignment Models

Assignment, AssignmentAttachment, AssignmentSubmission, SubmissionAttachment
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, FileExtensionValidator
from django.utils import timezone
from django.contrib.auth import get_user_model

from .managers import AssignmentManager

User = get_user_model()


class Assignment(models.Model):
    """
    Teacher-created assignment with attachments and due dates.
    """
    
    objects = AssignmentManager()
    
    module = models.ForeignKey('courses.PathModule', on_delete=models.CASCADE, related_name='assignments', db_index=True)
    
    title = models.CharField(max_length=255)
    description = models.TextField(help_text="Rich text/HTML instructions")
    
    due_date = models.DateTimeField(db_index=True)
    weight = models.PositiveIntegerField(default=100, validators=[MinValueValidator(1), MaxValueValidator(1000)])
    max_score = models.PositiveIntegerField(default=100)
    
    is_published = models.BooleanField(default=False, db_index=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    is_ai_generated = models.BooleanField(default=False)
    
    assigned_to = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True,
        related_name='personal_assignments', limit_choices_to={'role': 'student'}
    )
    
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        related_name='created_assignments', limit_choices_to={'role': 'teacher'}
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'assignments'
        verbose_name = 'Assignment'
        verbose_name_plural = 'Assignments'
        ordering = ['-due_date']
        indexes = [
            models.Index(fields=['module', 'is_published']),
            models.Index(fields=['due_date']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.module.path.label})"
    
    def is_overdue(self):
        return timezone.now() > self.due_date
    
    def days_until_due(self):
        delta = self.due_date - timezone.now()
        return delta.days


class AssignmentAttachment(models.Model):
    """Assignment attachments (files/links)."""
    
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='attachments')
    
    file = models.FileField(
        upload_to='assignments/attachments/',
        validators=[FileExtensionValidator(['pdf', 'doc', 'docx', 'ppt', 'pptx', 'jpg', 'png'])],
        null=True, blank=True
    )
    url = models.URLField(null=True, blank=True)
    title = models.CharField(max_length=255)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'assignment_attachments'
        verbose_name = 'Assignment Attachment'
        verbose_name_plural = 'Assignment Attachments'
    
    def __str__(self):
        return f"{self.assignment.title} - {self.title}"


class AssignmentSubmission(models.Model):
    """Student assignment submission with grading."""
    
    STATUS_CHOICES = [
        ('not_submitted', 'Not Submitted'),
        ('submitted', 'Submitted'),
        ('graded', 'Graded'),
        ('returned', 'Returned'),
    ]
    
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions', db_index=True)
    student = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='assignment_submissions',
        limit_choices_to={'role': 'student'}, db_index=True
    )
    
    content = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_submitted', db_index=True)
    
    grade = models.PositiveIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    feedback = models.TextField(blank=True)
    
    graded_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='graded_submissions', limit_choices_to={'role': 'teacher'}
    )
    
    submitted_at = models.DateTimeField(null=True, blank=True, db_index=True)
    graded_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'assignment_submissions'
        verbose_name = 'Assignment Submission'
        verbose_name_plural = 'Assignment Submissions'
        unique_together = ['assignment', 'student']
        ordering = ['-submitted_at']
        indexes = [
            models.Index(fields=['assignment', 'status']),
            models.Index(fields=['student', 'status']),
        ]
    
    def __str__(self):
        return f"{self.student.name} - {self.assignment.title}"
    
    def is_late(self):
        if not self.submitted_at:
            return False
        return self.submitted_at > self.assignment.due_date
    
    def can_resubmit(self):
        return self.status in ['not_submitted', 'submitted']


class SubmissionAttachment(models.Model):
    """Student submission file attachments."""
    
    submission = models.ForeignKey(AssignmentSubmission, on_delete=models.CASCADE, related_name='attachments')
    
    file = models.FileField(
        upload_to='assignments/submissions/',
        validators=[FileExtensionValidator(['pdf', 'doc', 'docx', 'jpg', 'png', 'zip'])]
    )
    filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'submission_attachments'
        verbose_name = 'Submission Attachment'
        verbose_name_plural = 'Submission Attachments'
    
    def __str__(self):
        return f"{self.submission} - {self.filename}"