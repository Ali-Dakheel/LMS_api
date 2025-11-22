from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model
from .managers import AssignmentProgressManager

User = get_user_model()

class AssignmentProgress(models.Model):
    """
    Tracks student progress on assignments.
    
    Features:
    - Submission status tracking
    - Grade tracking
    - Feedback storage
    - Timestamps (submitted, graded)
    - Late submission detection
    
    Denormalized for quick dashboard access.
    """
    
    objects = AssignmentProgressManager()
    
    STATUS_CHOICES = [
        ('not_submitted', 'Not Submitted'),
        ('submitted', 'Submitted'),
        ('graded', 'Graded'),
        ('returned', 'Returned'),
    ]
    
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='assignment_progress',
        limit_choices_to={'role': 'student'},
        db_index=True
    )
    
    assignment = models.ForeignKey(
        'assessments.Assignment',
        on_delete=models.CASCADE,
        related_name='student_progress',
        db_index=True
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='not_submitted',
        db_index=True
    )
    
    # Grading
    grade = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Grade (0-100)"
    )
    
    feedback = models.TextField(
        blank=True,
        help_text="Teacher feedback"
    )
    
    # Late submission
    is_late = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Was submission late?"
    )
    
    # Timestamps
    submitted_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True
    )
    
    graded_at = models.DateTimeField(
        null=True,
        blank=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'assignment_progress'
        verbose_name_plural = 'Assignment Progress'
        unique_together = ['student', 'assignment']
        ordering = ['-submitted_at']
        indexes = [
            models.Index(fields=['student', 'status']),
            models.Index(fields=['assignment', 'status']),
            models.Index(fields=['submitted_at']),
            models.Index(fields=['is_late']),
        ]
    
    def __str__(self):
        return f"{self.student.name} - {self.assignment.title} ({self.status})"
    
    def update_from_submission(self, submission):
        """
        Update progress from AssignmentSubmission.
        
        Args:
            submission: AssignmentSubmission instance
        """
        self.status = submission.status
        self.grade = submission.grade
        self.feedback = submission.feedback
        self.submitted_at = submission.submitted_at
        self.graded_at = submission.graded_at
        self.is_late = submission.is_late()
        self.save()
