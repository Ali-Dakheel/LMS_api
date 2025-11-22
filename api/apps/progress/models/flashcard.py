from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.contrib.auth import get_user_model
from decimal import Decimal
from .managers import FlashcardSetProgressManager

User = get_user_model()
class FlashcardSetProgress(models.Model):
    """
    Tracks student progress on flashcard sets (per module).
    
    Features:
    - Total cards in set
    - Mastered cards count
    - Progress percentage (SRS-based)
    - Next review schedule
    - Overall mastery status
    
    Aggregates FlashcardProgress records.
    """
    
    objects = FlashcardSetProgressManager()
    
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='flashcard_set_progress',
        limit_choices_to={'role': 'student'},
        db_index=True
    )
    
    module = models.ForeignKey(
        'courses.PathModule',
        on_delete=models.CASCADE,
        related_name='flashcard_progress',
        db_index=True
    )
    
    # Card counts
    total_cards = models.PositiveIntegerField(
        default=0,
        help_text="Total active flashcards in this module"
    )
    
    mastered_cards = models.PositiveIntegerField(
        default=0,
        help_text="Number of mastered cards (ease >= 2.5, interval >= 21)"
    )
    
    # Progress
    mastery_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Percentage of cards mastered"
    )
    
    # Review tracking
    cards_due_today = models.PositiveIntegerField(
        default=0,
        help_text="Number of cards due for review today"
    )
    
    next_review_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Next scheduled review time"
    )
    
    # Overall status
    is_fully_mastered = models.BooleanField(
        default=False,
        db_index=True,
        help_text="All cards are mastered"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'flashcard_set_progress'
        verbose_name_plural = 'Flashcard Set Progress'
        unique_together = ['student', 'module']
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['student', 'is_fully_mastered']),
            models.Index(fields=['module']),
            models.Index(fields=['next_review_at']),
        ]
    
    def __str__(self):
        return f"{self.student.name} - {self.module.title} ({self.mastered_cards}/{self.total_cards})"
    
    def calculate_progress(self):
        """
        Calculate flashcard mastery progress from individual FlashcardProgress records.
        
        Returns:
            dict: Updated progress metrics
        """
        from apps.assessments.models import Flashcard, FlashcardProgress
        
        # Get all active flashcards for this module
        flashcards = Flashcard.objects.filter(module=self.module, is_active=True)
        self.total_cards = flashcards.count()
        
        if self.total_cards == 0:
            self.mastery_percentage = Decimal('0.00')
            self.mastered_cards = 0
            self.cards_due_today = 0
            self.is_fully_mastered = False
            return
        
        # Get student's progress on these cards
        progress_records = FlashcardProgress.objects.filter(
            student=self.student,
            flashcard__in=flashcards
        )
        
        # Count mastered cards
        self.mastered_cards = progress_records.filter(is_mastered=True).count()
        
        # Calculate mastery percentage
        self.mastery_percentage = (Decimal(self.mastered_cards) / Decimal(self.total_cards)) * Decimal('100.00')
        
        # Count cards due today
        now = timezone.now()
        self.cards_due_today = progress_records.filter(
            next_review_at__lte=now
        ).count()
        
        # Check full mastery
        self.is_fully_mastered = (self.mastered_cards == self.total_cards)
        
        # Find next review date
        next_review = progress_records.filter(
            next_review_at__gt=now
        ).order_by('next_review_at').first()
        
        self.next_review_at = next_review.next_review_at if next_review else None
        
        self.save()
        
        return {
            'total_cards': self.total_cards,
            'mastered_cards': self.mastered_cards,
            'mastery_percentage': self.mastery_percentage,
            'cards_due_today': self.cards_due_today,
            'is_fully_mastered': self.is_fully_mastered,
        }
