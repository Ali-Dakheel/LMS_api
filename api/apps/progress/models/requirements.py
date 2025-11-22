from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.contrib.auth import get_user_model
from decimal import Decimal
from .managers import PathRequirementManager, PathRequirementStateManager
from .chat import ChatSessionMetric
from .assignment import AssignmentProgress
from .flashcard import FlashcardSetProgress

User = get_user_model()
class PathRequirement(models.Model):
    """
    Teacher-defined completion criteria for learning paths.
    
    Features:
    - Multiple requirement types (quiz, assignment, flashcard, chat)
    - Minimum scores/thresholds
    - Weighted requirements
    - Mandatory requirements (must pass to unlock)
    
    Used for gamified learning flow and path unlocking.
    """
    
    objects = PathRequirementManager()
    
    TYPE_CHOICES = [
        ('quiz', 'Quiz Minimum Score'),
        ('assignment', 'Assignment Minimum Grade'),
        ('flashcard', 'Flashcard Mastery %'),
        ('chat', 'Chat Minimum Messages'),
    ]
    
    path = models.ForeignKey(
        'courses.CoursePath',
        on_delete=models.CASCADE,
        related_name='requirements',
        db_index=True
    )
    
    requirement_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        db_index=True
    )
    
    # Target (quiz, assignment, module for flashcards)
    target_quiz = models.ForeignKey(
        'assessments.Quiz',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='path_requirements'
    )
    
    target_assignment = models.ForeignKey(
        'assessments.Assignment',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='path_requirements'
    )
    
    target_module = models.ForeignKey(
        'courses.PathModule',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='path_requirements',
        help_text="For flashcard/chat requirements"
    )
    
    # Thresholds
    minimum_score = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Minimum score % (for quiz/assignment)"
    )
    
    minimum_mastery = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Minimum mastery % (for flashcards)"
    )
    
    minimum_messages = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        help_text="Minimum chat messages"
    )
    
    # Weighting
    weight = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text="Weight for overall completion calculation"
    )
    
    is_mandatory = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Must complete to unlock next path"
    )
    
    # Order
    order = models.PositiveIntegerField(
        default=0,
        help_text="Display order"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'path_requirements'
        verbose_name_plural = 'Path Requirements'
        ordering = ['path', 'order']
        indexes = [
            models.Index(fields=['path', 'is_mandatory']),
            models.Index(fields=['requirement_type']),
        ]
    
    def __str__(self):
        return f"{self.path.label} - {self.get_requirement_type_display()}"
    
    def get_description(self):
        """Get human-readable requirement description."""
        if self.requirement_type == 'quiz':
            return f"Score at least {self.minimum_score}% on {self.target_quiz.title}"
        elif self.requirement_type == 'assignment':
            return f"Score at least {self.minimum_score}% on {self.target_assignment.title}"
        elif self.requirement_type == 'flashcard':
            return f"Master {self.minimum_mastery}% of flashcards in {self.target_module.title}"
        elif self.requirement_type == 'chat':
            return f"Send at least {self.minimum_messages} chat messages in {self.target_module.title}"
        return "Unknown requirement"

class PathRequirementState(models.Model):
    """
    Tracks student progress on individual path requirements.
    
    Features:
    - Per-requirement state tracking
    - Progress percentage (0-100)
    - Score tracking
    - Last event timestamp
    - Completion status
    
    Used for unlock logic and progress visualization.
    """
    
    objects = PathRequirementStateManager()
    
    STATE_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='requirement_states',
        limit_choices_to={'role': 'student'},
        db_index=True
    )
    
    requirement = models.ForeignKey(
        PathRequirement,
        on_delete=models.CASCADE,
        related_name='student_states',
        db_index=True
    )
    
    # State
    state = models.CharField(
        max_length=20,
        choices=STATE_CHOICES,
        default='not_started',
        db_index=True
    )
    
    # Progress
    progress_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Progress towards requirement (0-100)"
    )
    
    # Score tracking (for quiz/assignment requirements)
    current_score = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Current best score (if applicable)"
    )
    
    # Attempts
    attempt_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of attempts"
    )
    
    # Completion
    completed_at = models.DateTimeField(
        null=True,
        blank=True
    )
    
    # Last event
    last_event_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Last time student worked on this requirement"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'path_requirement_states'
        verbose_name_plural = 'Path Requirement States'
        unique_together = ['student', 'requirement']
        ordering = ['requirement__order']
        indexes = [
            models.Index(fields=['student', 'state']),
            models.Index(fields=['requirement', 'state']),
            models.Index(fields=['last_event_at']),
        ]
    
    def __str__(self):
        return f"{self.student.name} - {self.requirement} ({self.state})"
    
    def check_completion(self):
        """
        Check if requirement is met and update state.
        
        Returns:
            bool: True if requirement is met
        """
        requirement = self.requirement
        
        if requirement.requirement_type == 'quiz':
            # Check quiz score
            from apps.progress.models import QuizAttemptSummary
            
            summary = QuizAttemptSummary.objects.filter(
                student=self.student,
                quiz=requirement.target_quiz
            ).first()
            
            if summary and summary.best_score >= requirement.minimum_score:
                self.state = 'completed'
                self.progress_percentage = Decimal('100.00')
                self.current_score = summary.best_score
                self.completed_at = timezone.now()
                self.save()
                return True
            elif summary:
                self.state = 'in_progress'
                self.current_score = summary.best_score
                self.progress_percentage = min(
                    Decimal('99.99'),
                    (Decimal(summary.best_score) / Decimal(requirement.minimum_score)) * Decimal('100.00')
                )
                self.save()
        
        elif requirement.requirement_type == 'assignment':
            # Check assignment grade
            progress = AssignmentProgress.objects.filter(
                student=self.student,
                assignment=requirement.target_assignment,
                status='graded'
            ).first()
            
            if progress and progress.grade >= requirement.minimum_score:
                self.state = 'completed'
                self.progress_percentage = Decimal('100.00')
                self.current_score = progress.grade
                self.completed_at = timezone.now()
                self.save()
                return True
            elif progress:
                self.state = 'in_progress'
                self.current_score = progress.grade
                self.progress_percentage = min(
                    Decimal('99.99'),
                    (Decimal(progress.grade) / Decimal(requirement.minimum_score)) * Decimal('100.00')
                )
                self.save()
        
        elif requirement.requirement_type == 'flashcard':
            # Check flashcard mastery
            flashcard_progress = FlashcardSetProgress.objects.filter(
                student=self.student,
                module=requirement.target_module
            ).first()
            
            if flashcard_progress and flashcard_progress.mastery_percentage >= requirement.minimum_mastery:
                self.state = 'completed'
                self.progress_percentage = Decimal('100.00')
                self.completed_at = timezone.now()
                self.save()
                return True
            elif flashcard_progress:
                self.state = 'in_progress'
                self.progress_percentage = min(
                    Decimal('99.99'),
                    (flashcard_progress.mastery_percentage / Decimal(requirement.minimum_mastery)) * Decimal('100.00')
                )
                self.save()
        
        elif requirement.requirement_type == 'chat':
            # Check chat messages
            metric = ChatSessionMetric.objects.filter(
                student=self.student,
                module=requirement.target_module
            ).first()
            
            if metric and metric.total_messages >= requirement.minimum_messages:
                self.state = 'completed'
                self.progress_percentage = Decimal('100.00')
                self.completed_at = timezone.now()
                self.save()
                return True
            elif metric:
                self.state = 'in_progress'
                self.progress_percentage = min(
                    Decimal('99.99'),
                    (Decimal(metric.total_messages) / Decimal(requirement.minimum_messages)) * Decimal('100.00')
                )
                self.save()
        
        return False
    
    def is_completed(self):
        """Check if requirement is completed."""
        return self.state == 'completed'