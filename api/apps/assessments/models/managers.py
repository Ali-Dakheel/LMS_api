"""
Assessments App Managers

Custom managers for efficient queries on assessment models.
"""

from django.db import models
from django.db.models import Q, Count, Avg, Max, Prefetch
from django.utils import timezone


# ============================================================================
# ASSIGNMENT MANAGERS
# ============================================================================

class AssignmentQuerySet(models.QuerySet):
    """Custom QuerySet for Assignment."""
    
    def published_only(self):
        """Filter published assignments."""
        return self.filter(is_published=True)
    
    def for_module(self, module):
        """Filter by module."""
        return self.filter(module=module)
    
    def for_student(self, student):
        """
        Filter assignments visible to student.
        
        Includes:
        - Published assignments in student's enrolled modules
        - Personal assignments assigned to this student
        """
        return self.filter(
            Q(module__path__offering__enrollments__student=student, is_published=True) |
            Q(assigned_to=student)
        ).distinct()
    
    def upcoming(self):
        """Filter upcoming assignments (not yet due)."""
        return self.filter(due_date__gt=timezone.now())
    
    def overdue(self):
        """Filter overdue assignments."""
        return self.filter(due_date__lt=timezone.now())
    
    def with_submissions(self):
        """Prefetch submissions."""
        return self.prefetch_related('submissions', 'submissions__student')


class AssignmentManager(models.Manager):
    """Manager for Assignment."""
    
    def get_queryset(self):
        return AssignmentQuerySet(self.model, using=self._db)
    
    def published_only(self):
        return self.get_queryset().published_only()
    
    def for_module(self, module):
        return self.get_queryset().for_module(module)
    
    def for_student(self, student):
        return self.get_queryset().for_student(student)
    
    def upcoming(self):
        return self.get_queryset().upcoming()
    
    def overdue(self):
        return self.get_queryset().overdue()


# ============================================================================
# QUIZ MANAGERS
# ============================================================================

class QuizQuerySet(models.QuerySet):
    """Custom QuerySet for Quiz."""
    
    def published_only(self):
        """Filter published quizzes."""
        return self.filter(is_published=True)
    
    def for_module(self, module):
        """Filter by module."""
        return self.filter(module=module)
    
    def by_difficulty(self, difficulty):
        """Filter by difficulty level."""
        return self.filter(difficulty=difficulty)
    
    def practice_mode(self):
        """Filter practice quizzes."""
        return self.filter(is_practice=True)
    
    def with_questions(self):
        """Prefetch questions."""
        return self.prefetch_related('questions')


class QuizManager(models.Manager):
    """Manager for Quiz."""
    
    def get_queryset(self):
        return QuizQuerySet(self.model, using=self._db)
    
    def published_only(self):
        return self.get_queryset().published_only()
    
    def for_module(self, module):
        return self.get_queryset().for_module(module)
    
    def by_difficulty(self, difficulty):
        return self.get_queryset().by_difficulty(difficulty)
    
    def practice_mode(self):
        return self.get_queryset().practice_mode()


# ============================================================================
# QUIZ ATTEMPT MANAGERS
# ============================================================================

class QuizAttemptQuerySet(models.QuerySet):
    """Custom QuerySet for QuizAttempt."""
    
    def for_student(self, student):
        """Filter by student."""
        return self.filter(student=student)
    
    def for_quiz(self, quiz):
        """Filter by quiz."""
        return self.filter(quiz=quiz)
    
    def submitted_only(self):
        """Filter submitted attempts."""
        return self.filter(status='submitted')
    
    def in_progress(self):
        """Filter in-progress attempts."""
        return self.filter(status='in_progress')
    
    def passed(self):
        """Filter passed attempts."""
        return self.filter(passed=True)
    
    def failed(self):
        """Filter failed attempts."""
        return self.filter(passed=False)
    
    def with_answers(self):
        """Prefetch answers and questions."""
        return self.prefetch_related('answers', 'answers__question')
    
    def best_score_per_student(self):
        """Get best score per student per quiz."""
        return self.values('student', 'quiz').annotate(
            best_score=Max('score')
        )


class QuizAttemptManager(models.Manager):
    """Manager for QuizAttempt."""
    
    def get_queryset(self):
        return QuizAttemptQuerySet(self.model, using=self._db)
    
    def for_student(self, student):
        return self.get_queryset().for_student(student)
    
    def for_quiz(self, quiz):
        return self.get_queryset().for_quiz(quiz)
    
    def submitted_only(self):
        return self.get_queryset().submitted_only()
    
    def in_progress(self):
        return self.get_queryset().in_progress()
    
    def passed(self):
        return self.get_queryset().passed()


# ============================================================================
# FLASHCARD MANAGERS
# ============================================================================

class FlashcardQuerySet(models.QuerySet):
    """Custom QuerySet for Flashcard."""
    
    def active_only(self):
        """Filter active flashcards."""
        return self.filter(is_active=True)
    
    def for_module(self, module):
        """Filter by module."""
        return self.filter(module=module)
    
    def ai_generated(self):
        """Filter AI-generated cards."""
        return self.filter(is_ai_generated=True)


class FlashcardManager(models.Manager):
    """Manager for Flashcard."""
    
    def get_queryset(self):
        return FlashcardQuerySet(self.model, using=self._db)
    
    def active_only(self):
        return self.get_queryset().active_only()
    
    def for_module(self, module):
        return self.get_queryset().for_module(module)


# ============================================================================
# FLASHCARD PROGRESS MANAGERS
# ============================================================================

class FlashcardProgressQuerySet(models.QuerySet):
    """Custom QuerySet for FlashcardProgress."""
    
    def for_student(self, student):
        """Filter by student."""
        return self.filter(student=student)
    
    def for_module(self, module):
        """Filter by module (through flashcard)."""
        return self.filter(flashcard__module=module)
    
    def due_for_review(self):
        """Filter cards due for review."""
        return self.filter(
            Q(next_review_at__isnull=True) |
            Q(next_review_at__lte=timezone.now())
        )
    
    def mastered(self):
        """Filter mastered cards."""
        return self.filter(is_mastered=True)
    
    def not_mastered(self):
        """Filter not mastered cards."""
        return self.filter(is_mastered=False)
    
    def with_flashcard(self):
        """Select related flashcard."""
        return self.select_related('flashcard', 'flashcard__module')


class FlashcardProgressManager(models.Manager):
    """Manager for FlashcardProgress."""
    
    def get_queryset(self):
        return FlashcardProgressQuerySet(self.model, using=self._db)
    
    def for_student(self, student):
        return self.get_queryset().for_student(student)
    
    def for_module(self, module):
        return self.get_queryset().for_module(module)
    
    def due_for_review(self):
        return self.get_queryset().due_for_review()
    
    def mastered(self):
        return self.get_queryset().mastered()