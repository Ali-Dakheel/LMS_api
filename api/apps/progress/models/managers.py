"""
Progress App Managers

Custom model managers for:
- LessonProgress (completion filtering, time tracking)
- LearningPathProgress (status filtering, unlock logic)
- QuizAttemptSummary (passed/failed, score filtering)
- FlashcardSetProgress (mastery filtering)
- AssignmentProgress (status filtering, late submissions)
- TopicAnalytics (weak topics, strength levels)
- PathRequirement (mandatory requirements)
- PathRequirementState (completion tracking)
"""

from django.db import models
from django.utils import timezone
from django.db.models import Avg, Count, Sum, Q, F
from decimal import Decimal


class LessonProgressManager(models.Manager):
    """Custom manager for LessonProgress model."""
    
    def completed(self):
        """Get all completed lessons."""
        return self.filter(is_completed=True)
    
    def in_progress(self):
        """Get lessons that are in progress (0 < completion < 100)."""
        return self.filter(
            is_completed=False,
            completion_percentage__gt=0
        )
    
    def not_started(self):
        """Get lessons not yet started (completion = 0)."""
        return self.filter(completion_percentage=0)
    
    def for_student(self, student):
        """
        Get all lesson progress for a student.
        
        Args:
            student: User instance
        
        Returns:
            QuerySet of LessonProgress
        """
        return self.filter(student=student)
    
    def for_module(self, module):
        """
        Get all student progress for a specific module.
        
        Args:
            module: PathModule instance
        
        Returns:
            QuerySet of LessonProgress
        """
        return self.filter(module=module)
    
    def recent(self, days=7):
        """
        Get recently accessed lessons.
        
        Args:
            days: Number of days to look back
        
        Returns:
            QuerySet of recent LessonProgress
        """
        cutoff = timezone.now() - timezone.timedelta(days=days)
        return self.filter(last_accessed_at__gte=cutoff)
    
    def with_time_spent(self, min_seconds=0):
        """
        Get lessons with minimum time spent.
        
        Args:
            min_seconds: Minimum seconds spent
        
        Returns:
            QuerySet
        """
        return self.filter(time_spent_seconds__gte=min_seconds)


class LearningPathProgressManager(models.Manager):
    """Custom manager for LearningPathProgress model."""
    
    def not_started(self):
        """Get paths not started."""
        return self.filter(status='not_started')
    
    def in_progress(self):
        """Get paths in progress."""
        return self.filter(status='in_progress')
    
    def completed(self):
        """Get completed paths."""
        return self.filter(status='completed')
    
    def locked(self):
        """Get locked paths."""
        return self.filter(status='locked')
    
    def unlocked(self):
        """Get unlocked paths."""
        return self.filter(is_unlocked=True)
    
    def for_student(self, student):
        """
        Get all path progress for a student.
        
        Args:
            student: User instance
        
        Returns:
            QuerySet of LearningPathProgress
        """
        return self.filter(student=student)
    
    def for_path(self, path):
        """
        Get all student progress for a specific path.
        
        Args:
            path: CoursePath instance
        
        Returns:
            QuerySet of LearningPathProgress
        """
        return self.filter(path=path)
    
    def by_completion(self, min_percentage=0, max_percentage=100):
        """
        Filter by completion percentage range.
        
        Args:
            min_percentage: Minimum completion %
            max_percentage: Maximum completion %
        
        Returns:
            QuerySet
        """
        return self.filter(
            completion_percentage__gte=min_percentage,
            completion_percentage__lte=max_percentage
        )


class QuizAttemptSummaryManager(models.Manager):
    """Custom manager for QuizAttemptSummary model."""
    
    def passed(self):
        """Get summaries where student has passed."""
        return self.filter(has_passed=True)
    
    def not_passed(self):
        """Get summaries where student hasn't passed yet."""
        return self.filter(has_passed=False)
    
    def for_student(self, student):
        """
        Get all quiz summaries for a student.
        
        Args:
            student: User instance
        
        Returns:
            QuerySet of QuizAttemptSummary
        """
        return self.filter(student=student)
    
    def for_quiz(self, quiz):
        """
        Get all student summaries for a quiz.
        
        Args:
            quiz: Quiz instance
        
        Returns:
            QuerySet of QuizAttemptSummary
        """
        return self.filter(quiz=quiz)
    
    def by_score(self, min_score=0, max_score=100):
        """
        Filter by best score range.
        
        Args:
            min_score: Minimum score
            max_score: Maximum score
        
        Returns:
            QuerySet
        """
        return self.filter(
            best_score__gte=min_score,
            best_score__lte=max_score
        )
    
    def recent_attempts(self, days=7):
        """
        Get summaries with recent attempts.
        
        Args:
            days: Number of days to look back
        
        Returns:
            QuerySet
        """
        cutoff = timezone.now() - timezone.timedelta(days=days)
        return self.filter(last_attempt_at__gte=cutoff)
    
    def with_multiple_attempts(self):
        """Get summaries with more than one attempt."""
        return self.filter(total_attempts__gt=1)


class FlashcardSetProgressManager(models.Manager):
    """Custom manager for FlashcardSetProgress model."""
    
    def fully_mastered(self):
        """Get fully mastered flashcard sets."""
        return self.filter(is_fully_mastered=True)
    
    def in_progress(self):
        """Get sets that are in progress (not fully mastered)."""
        return self.filter(is_fully_mastered=False, mastered_cards__gt=0)
    
    def not_started(self):
        """Get sets not yet started."""
        return self.filter(mastered_cards=0)
    
    def for_student(self, student):
        """
        Get all flashcard progress for a student.
        
        Args:
            student: User instance
        
        Returns:
            QuerySet of FlashcardSetProgress
        """
        return self.filter(student=student)
    
    def for_module(self, module):
        """
        Get all student progress for a module's flashcards.
        
        Args:
            module: PathModule instance
        
        Returns:
            QuerySet of FlashcardSetProgress
        """
        return self.filter(module=module)
    
    def by_mastery(self, min_percentage=0, max_percentage=100):
        """
        Filter by mastery percentage range.
        
        Args:
            min_percentage: Minimum mastery %
            max_percentage: Maximum mastery %
        
        Returns:
            QuerySet
        """
        return self.filter(
            mastery_percentage__gte=min_percentage,
            mastery_percentage__lte=max_percentage
        )
    
    def due_for_review(self):
        """Get sets with cards due for review today."""
        return self.filter(cards_due_today__gt=0)


class AssignmentProgressManager(models.Manager):
    """Custom manager for AssignmentProgress model."""
    
    def not_submitted(self):
        """Get not submitted assignments."""
        return self.filter(status='not_submitted')
    
    def submitted(self):
        """Get submitted (but not graded) assignments."""
        return self.filter(status='submitted')
    
    def graded(self):
        """Get graded assignments."""
        return self.filter(status='graded')
    
    def late_submissions(self):
        """Get late submissions."""
        return self.filter(is_late=True)
    
    def for_student(self, student):
        """
        Get all assignment progress for a student.
        
        Args:
            student: User instance
        
        Returns:
            QuerySet of AssignmentProgress
        """
        return self.filter(student=student)
    
    def for_assignment(self, assignment):
        """
        Get all student progress for an assignment.
        
        Args:
            assignment: Assignment instance
        
        Returns:
            QuerySet of AssignmentProgress
        """
        return self.filter(assignment=assignment)
    
    def by_grade(self, min_grade=0, max_grade=100):
        """
        Filter by grade range.
        
        Args:
            min_grade: Minimum grade
            max_grade: Maximum grade
        
        Returns:
            QuerySet
        """
        return self.filter(
            grade__isnull=False,
            grade__gte=min_grade,
            grade__lte=max_grade
        )
    
    def pending_grading(self):
        """Get assignments awaiting grading."""
        return self.filter(status='submitted', grade__isnull=True)


class TopicAnalyticsManager(models.Manager):
    """Custom manager for TopicAnalytics model."""
    
    def weak_topics(self):
        """Get weak topics (need attention)."""
        return self.filter(strength_level='weak')
    
    def developing_topics(self):
        """Get developing topics."""
        return self.filter(strength_level='developing')
    
    def proficient_topics(self):
        """Get proficient topics."""
        return self.filter(strength_level='proficient')
    
    def strong_topics(self):
        """Get strong topics."""
        return self.filter(strength_level='strong')
    
    def for_student(self, student):
        """
        Get all topic analytics for a student.
        
        Args:
            student: User instance
        
        Returns:
            QuerySet of TopicAnalytics
        """
        return self.filter(student=student)
    
    def for_course(self, course):
        """
        Get all student analytics for a course.
        
        Args:
            course: Course instance
        
        Returns:
            QuerySet of TopicAnalytics
        """
        return self.filter(course=course)
    
    def by_strength(self, min_score=0, max_score=100):
        """
        Filter by strength score range.
        
        Args:
            min_score: Minimum strength score
            max_score: Maximum strength score
        
        Returns:
            QuerySet
        """
        return self.filter(
            strength_score__gte=min_score,
            strength_score__lte=max_score
        )
    
    def recently_analyzed(self, days=7):
        """
        Get analytics updated in last N days.
        
        Args:
            days: Number of days
        
        Returns:
            QuerySet
        """
        cutoff = timezone.now() - timezone.timedelta(days=days)
        return self.filter(analyzed_at__gte=cutoff)


class PathRequirementManager(models.Manager):
    """Custom manager for PathRequirement model."""
    
    def mandatory(self):
        """Get mandatory requirements."""
        return self.filter(is_mandatory=True)
    
    def optional(self):
        """Get optional requirements."""
        return self.filter(is_mandatory=False)
    
    def for_path(self, path):
        """
        Get all requirements for a path.
        
        Args:
            path: CoursePath instance
        
        Returns:
            QuerySet of PathRequirement ordered by order field
        """
        return self.filter(path=path).order_by('order')
    
    def by_type(self, requirement_type):
        """
        Filter by requirement type.
        
        Args:
            requirement_type: 'quiz', 'assignment', 'flashcard', 'chat'
        
        Returns:
            QuerySet
        """
        return self.filter(requirement_type=requirement_type)
    
    def quiz_requirements(self):
        """Get all quiz requirements."""
        return self.filter(requirement_type='quiz')
    
    def assignment_requirements(self):
        """Get all assignment requirements."""
        return self.filter(requirement_type='assignment')
    
    def flashcard_requirements(self):
        """Get all flashcard requirements."""
        return self.filter(requirement_type='flashcard')
    
    def chat_requirements(self):
        """Get all chat requirements."""
        return self.filter(requirement_type='chat')


class PathRequirementStateManager(models.Manager):
    """Custom manager for PathRequirementState model."""
    
    def not_started(self):
        """Get requirements not yet started."""
        return self.filter(state='not_started')
    
    def in_progress(self):
        """Get requirements in progress."""
        return self.filter(state='in_progress')
    
    def completed(self):
        """Get completed requirements."""
        return self.filter(state='completed')
    
    def failed(self):
        """Get failed requirements."""
        return self.filter(state='failed')
    
    def for_student(self, student):
        """
        Get all requirement states for a student.
        
        Args:
            student: User instance
        
        Returns:
            QuerySet of PathRequirementState
        """
        return self.filter(student=student)
    
    def for_requirement(self, requirement):
        """
        Get all student states for a requirement.
        
        Args:
            requirement: PathRequirement instance
        
        Returns:
            QuerySet of PathRequirementState
        """
        return self.filter(requirement=requirement)
    
    def for_path(self, path, student):
        """
        Get all requirement states for a student in a specific path.
        
        Args:
            path: CoursePath instance
            student: User instance
        
        Returns:
            QuerySet of PathRequirementState
        """
        return self.filter(
            student=student,
            requirement__path=path
        ).order_by('requirement__order')
    
    def mandatory_completed(self, student, path):
        """
        Check if all mandatory requirements are completed for a path.
        
        Args:
            student: User instance
            path: CoursePath instance
        
        Returns:
            bool: True if all mandatory requirements are completed
        """
        mandatory_requirements = path.requirements.filter(is_mandatory=True)
        
        if not mandatory_requirements.exists():
            return True
        
        completed_count = self.filter(
            student=student,
            requirement__in=mandatory_requirements,
            state='completed'
        ).count()
        
        return completed_count == mandatory_requirements.count()