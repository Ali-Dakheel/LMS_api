from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.contrib.auth import get_user_model
from decimal import Decimal
from .managers import QuizAttemptSummaryManager

User = get_user_model()

class QuizAttemptSummary(models.Model):
    """
    Aggregated summary of student's quiz performance per quiz.
    
    Features:
    - Best score tracking
    - Last score tracking
    - Total attempts count
    - Pass/fail status
    - Per-question progress
    - Average time taken
    
    Denormalized for fast dashboard queries.
    """
    
    objects = QuizAttemptSummaryManager()
    
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='quiz_summaries',
        limit_choices_to={'role': 'student'},
        db_index=True
    )
    
    quiz = models.ForeignKey(
        'assessments.Quiz',
        on_delete=models.CASCADE,
        related_name='student_summaries',
        db_index=True
    )
    
    # Score tracking
    best_score = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Best score achieved (0-100)"
    )
    
    last_score = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Most recent score (0-100)"
    )
    
    average_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Average score across all attempts"
    )
    
    # Attempts
    total_attempts = models.PositiveIntegerField(
        default=0,
        help_text="Total number of attempts"
    )
    
    passed_attempts = models.PositiveIntegerField(
        default=0,
        help_text="Number of attempts that passed"
    )
    
    # Status
    has_passed = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Has student ever passed this quiz?"
    )
    
    # Timing
    average_time_seconds = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Average time taken per attempt (seconds)"
    )
    
    # Per-question progress (JSON)
    question_progress = models.JSONField(
        default=dict,
        blank=True,
        help_text="Per-question correctness tracking"
    )
    
    # Timestamps
    first_attempt_at = models.DateTimeField(
        null=True,
        blank=True
    )
    last_attempt_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'quiz_attempt_summaries'
        verbose_name_plural = 'Quiz Attempt Summaries'
        unique_together = ['student', 'quiz']
        ordering = ['-last_attempt_at']
        indexes = [
            models.Index(fields=['student', 'has_passed']),
            models.Index(fields=['quiz']),
            models.Index(fields=['last_attempt_at']),
        ]
    
    def __str__(self):
        return f"{self.student.name} - {self.quiz.title} (Best: {self.best_score}%)"
    
    def update_from_attempt(self, attempt):
        """
        Update summary from a quiz attempt.
        
        Args:
            attempt: QuizAttempt instance
        """
        from apps.assessments.models import QuizAttempt
        
        # Update scores
        if attempt.score > self.best_score:
            self.best_score = attempt.score
        
        self.last_score = attempt.score
        
        # Update attempts
        self.total_attempts += 1
        if attempt.passed:
            self.passed_attempts += 1
            self.has_passed = True
        
        # Calculate average score
        all_attempts = QuizAttempt.objects.filter(
            student=self.student,
            quiz=self.quiz,
            status='submitted'
        )
        
        scores = [a.score for a in all_attempts if a.score is not None]
        if scores:
            self.average_score = Decimal(sum(scores)) / Decimal(len(scores))
        
        # Calculate average time
        times = [a.time_taken_seconds for a in all_attempts if a.time_taken_seconds is not None]
        if times:
            self.average_time_seconds = sum(times) // len(times)
        
        # Update timestamps
        if not self.first_attempt_at:
            self.first_attempt_at = attempt.started_at
        self.last_attempt_at = attempt.submitted_at or timezone.now()
        
        self.save()

