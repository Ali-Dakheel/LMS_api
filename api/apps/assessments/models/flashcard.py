"""
Flashcard Models with SRS
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model

from .managers import FlashcardManager, FlashcardProgressManager

User = get_user_model()


class Flashcard(models.Model):
    """Flashcard for spaced repetition."""
    
    objects = FlashcardManager()
    
    module = models.ForeignKey('courses.PathModule', on_delete=models.CASCADE, related_name='flashcards', db_index=True)
    
    question = models.TextField()
    answer = models.TextField()
    hint = models.TextField(blank=True)
    
    order = models.PositiveIntegerField(default=0)
    is_ai_generated = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True, db_index=True)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_flashcards')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'flashcards'
        verbose_name = 'Flashcard'
        verbose_name_plural = 'Flashcards'
        ordering = ['module', 'order']
    
    def __str__(self):
        return f"{self.module.title} - {self.question[:50]}"


class FlashcardProgress(models.Model):
    """SRS progress tracking (SM-2 algorithm)."""
    
    objects = FlashcardProgressManager()
    
    flashcard = models.ForeignKey(Flashcard, on_delete=models.CASCADE, related_name='progress_records', db_index=True)
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='flashcard_progress', db_index=True)
    
    # SRS parameters
    ease_factor = models.FloatField(default=2.5, validators=[MinValueValidator(1.3), MaxValueValidator(2.5)])
    interval_days = models.PositiveIntegerField(default=1)
    repetitions = models.PositiveIntegerField(default=0)
    
    last_reviewed_at = models.DateTimeField(null=True, blank=True, db_index=True)
    next_review_at = models.DateTimeField(null=True, blank=True, db_index=True)
    
    total_reviews = models.PositiveIntegerField(default=0)
    correct_reviews = models.PositiveIntegerField(default=0)
    
    is_mastered = models.BooleanField(default=False, db_index=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'flashcard_progress'
        verbose_name = 'Flashcard Progress'
        verbose_name_plural = 'Flashcard Progress'
        unique_together = ['flashcard', 'student']
        ordering = ['next_review_at']
    
    def __str__(self):
        return f"{self.student.name} - {self.flashcard.question[:30]}"
    
    def update_srs(self, quality):
        """Update SRS (0-5 quality)."""
        from apps.assessments.services import calculate_srs_interval
        
        self.total_reviews += 1
        if quality >= 3:
            self.correct_reviews += 1
        
        new_params = calculate_srs_interval(self.ease_factor, self.interval_days, self.repetitions, quality)
        
        self.ease_factor = new_params['ease_factor']
        self.interval_days = new_params['interval']
        self.repetitions = new_params['repetitions']
        self.last_reviewed_at = timezone.now()
        self.next_review_at = timezone.now() + timedelta(days=self.interval_days)
        self.is_mastered = (self.ease_factor >= 2.5 and self.interval_days >= 21)
        
        self.save()
        return new_params