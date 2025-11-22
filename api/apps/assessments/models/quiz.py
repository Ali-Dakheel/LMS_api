"""
Quiz Models

Quiz, QuizQuestion, QuizAttempt, QuizAttemptAnswer
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.utils import timezone

from .managers import QuizManager, QuizAttemptManager

User = get_user_model()


class Quiz(models.Model):
    """Quiz with multiple question types and timed mode."""
    
    objects = QuizManager()
    
    DIFFICULTY_CHOICES = [('easy', 'Easy'), ('medium', 'Medium'), ('hard', 'Hard')]
    
    module = models.ForeignKey('courses.PathModule', on_delete=models.CASCADE, related_name='quizzes', db_index=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='medium', db_index=True)
    
    duration_minutes = models.PositiveIntegerField(default=30)
    passing_score = models.PositiveIntegerField(default=70, validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    is_practice = models.BooleanField(default=False)
    show_answers_after = models.BooleanField(default=True)
    
    is_published = models.BooleanField(default=False, db_index=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    is_ai_generated = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_quizzes')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'quizzes'
        verbose_name = 'Quiz'
        verbose_name_plural = 'Quizzes'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['module', 'is_published']),
            models.Index(fields=['difficulty']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.get_difficulty_display()})"


class QuizQuestion(models.Model):
    """Quiz question (MCQ, Fill, TF, Matching)."""
    
    TYPE_CHOICES = [
        ('mcq', 'Multiple Choice'),
        ('fill', 'Fill in the Blank'),
        ('tf', 'True/False'),
        ('match', 'Matching'),
    ]
    
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions', db_index=True)
    question_type = models.CharField(max_length=10, choices=TYPE_CHOICES, db_index=True)
    question_text = models.TextField()
    
    options = models.JSONField(null=True, blank=True)
    correct_answer = models.TextField()
    matching_pairs = models.JSONField(null=True, blank=True)
    
    explanation = models.TextField(blank=True)
    points = models.PositiveIntegerField(default=1)
    order = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'quiz_questions'
        verbose_name = 'Quiz Question'
        verbose_name_plural = 'Quiz Questions'
        ordering = ['quiz', 'order']
    
    def __str__(self):
        return f"{self.quiz.title} - Q{self.order + 1}"


class QuizAttempt(models.Model):
    """Student quiz attempt with scoring."""
    
    objects = QuizAttemptManager()
    
    STATUS_CHOICES = [('in_progress', 'In Progress'), ('submitted', 'Submitted'), ('graded', 'Graded')]
    
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts', db_index=True)
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quiz_attempts', db_index=True)
    
    attempt_number = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress', db_index=True)
    
    score = models.PositiveIntegerField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(100)])
    total_points_earned = models.PositiveIntegerField(default=0)
    total_points_possible = models.PositiveIntegerField(default=0)
    
    started_at = models.DateTimeField(auto_now_add=True, db_index=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    time_taken_seconds = models.PositiveIntegerField(null=True, blank=True)
    
    passed = models.BooleanField(default=False, db_index=True)
    
    class Meta:
        db_table = 'quiz_attempts'
        verbose_name = 'Quiz Attempt'
        verbose_name_plural = 'Quiz Attempts'
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.student.name} - {self.quiz.title} (Attempt {self.attempt_number})"
    
    def calculate_score(self):
        if self.total_points_possible == 0:
            self.score = 0
        else:
            self.score = int((self.total_points_earned / self.total_points_possible) * 100)
        self.passed = self.score >= self.quiz.passing_score
        self.save(update_fields=['score', 'passed'])


class QuizAttemptAnswer(models.Model):
    """Individual answer to quiz question."""
    
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='answers', db_index=True)
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE, related_name='student_answers')
    
    answer = models.TextField(blank=True)
    matching_answer = models.JSONField(null=True, blank=True)
    
    is_correct = models.BooleanField(default=False)
    points_earned = models.PositiveIntegerField(default=0)
    answered_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'quiz_attempt_answers'
        verbose_name = 'Quiz Attempt Answer'
        verbose_name_plural = 'Quiz Attempt Answers'
        unique_together = ['attempt', 'question']
    
    def __str__(self):
        return f"{self.attempt} - Q{self.question.order + 1}"
    
    def check_answer(self):
        """Auto-grade answer."""
        q = self.question
        
        if q.question_type in ['mcq', 'fill', 'tf']:
            self.is_correct = self.answer.strip().lower() == q.correct_answer.strip().lower()
        
        elif q.question_type == 'match':
            if self.matching_answer and q.matching_pairs:
                correct = {(p['left'], p['right']) for p in q.matching_pairs}
                student = {(p['left'], p['right']) for p in self.matching_answer}
                self.is_correct = correct == student
            else:
                self.is_correct = False
        
        self.points_earned = q.points if self.is_correct else 0
        self.save(update_fields=['is_correct', 'points_earned'])
        return self.is_correct