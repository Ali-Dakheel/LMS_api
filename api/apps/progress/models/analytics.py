from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model
from decimal import Decimal
from .managers import TopicAnalyticsManager

User = get_user_model()

class TopicAnalytics(models.Model):
    """
    AI-analyzed topic strengths and weaknesses.
    
    Features:
    - Per-topic strength scores (0-100)
    - Weak topics identification
    - AI-generated insights
    - Recommendation engine data
    
    Used for personalized learning recommendations.
    """
    
    objects = TopicAnalyticsManager()
    
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='topic_analytics',
        limit_choices_to={'role': 'student'},
        db_index=True
    )
    
    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.CASCADE,
        related_name='student_analytics',
        db_index=True,
        help_text="Course this analytics belongs to"
    )
    
    topic_name = models.CharField(
        max_length=255,
        db_index=True,
        help_text="Topic/category name (e.g., Grammar, Algebra)"
    )
    
    # Strength scoring
    strength_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="AI-calculated strength score (0-100)"
    )
    
    STRENGTH_LEVEL_CHOICES = [
        ('weak', 'Weak'),
        ('developing', 'Developing'),
        ('proficient', 'Proficient'),
        ('strong', 'Strong'),
    ]
    
    strength_level = models.CharField(
        max_length=20,
        choices=STRENGTH_LEVEL_CHOICES,
        default='developing',
        db_index=True
    )
    
    # AI insights
    ai_insights = models.TextField(
        blank=True,
        help_text="AI-generated insights about performance"
    )
    
    recommendations = models.JSONField(
        default=list,
        blank=True,
        help_text="AI-recommended actions/content"
    )
    
    # Data sources (for score calculation)
    quiz_average = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Average quiz score for this topic"
    )
    
    assignment_average = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Average assignment grade for this topic"
    )
    
    flashcard_mastery = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Flashcard mastery percentage"
    )
    
    # Last analysis
    analyzed_at = models.DateTimeField(
        auto_now=True,
        db_index=True,
        help_text="When this analysis was last updated"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'topic_analytics'
        verbose_name_plural = 'Topic Analytics'
        unique_together = ['student', 'course', 'topic_name']
        ordering = ['student', 'strength_score']
        indexes = [
            models.Index(fields=['student', 'strength_level']),
            models.Index(fields=['course', 'topic_name']),
            models.Index(fields=['strength_score']),
            models.Index(fields=['analyzed_at']),
        ]
    
    def __str__(self):
        return f"{self.student.name} - {self.topic_name} ({self.strength_score})"
    
    def calculate_strength_level(self):
        """
        Calculate strength level from score.
        
        Scoring:
        - 0-40: Weak
        - 41-60: Developing
        - 61-80: Proficient
        - 81-100: Strong
        """
        score = float(self.strength_score)
        
        if score <= 40:
            self.strength_level = 'weak'
        elif score <= 60:
            self.strength_level = 'developing'
        elif score <= 80:
            self.strength_level = 'proficient'
        else:
            self.strength_level = 'strong'
        
        self.save(update_fields=['strength_level'])
    
    def is_weak_topic(self):
        """Check if this is a weak topic (needs attention)."""
        return self.strength_level == 'weak'
