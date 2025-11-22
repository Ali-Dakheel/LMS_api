"""
Unit tests for Progress app models.

Tests:
- LessonProgress (completion tracking, time spent)
- LearningPathProgress (path completion, unlock logic)
- QuizAttemptSummary (score tracking, aggregation)
- FlashcardSetProgress (mastery calculation)
- AssignmentProgress (submission tracking)
- ChatSessionMetric (message aggregation)
- TopicAnalytics (strength scoring, weak topics)
- PathRequirement (requirement definition)
- PathRequirementState (completion checking, unlock logic)
"""

import pytest
from datetime import timedelta
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from decimal import Decimal

from apps.progress.models import (
    LessonProgress,
    LearningPathProgress,
    QuizAttemptSummary,
    FlashcardSetProgress,
    AssignmentProgress,
    ChatSessionMetric,
    TopicAnalytics,
    PathRequirement,
    PathRequirementState,
)


# ============================================================================
# LESSON PROGRESS MODEL TESTS
# ============================================================================

@pytest.mark.django_db
class TestLessonProgressModel:
    """Test LessonProgress model."""
    
    def test_create_lesson_progress(self, lesson_progress_started):
        """Test creating lesson progress."""
        assert lesson_progress_started.completion_percentage == Decimal('45.00')
        assert lesson_progress_started.is_completed is False
        assert lesson_progress_started.time_spent_seconds == 900
        assert lesson_progress_started.view_count == 3
    
    def test_lesson_progress_str_representation(self, lesson_progress_started, student_user, module):
        """Test __str__ method."""
        str_repr = str(lesson_progress_started)
        assert student_user.name in str_repr
        assert module.title in str_repr
        assert '45' in str_repr
    
    def test_mark_completed(self, lesson_progress_started):
        """Test mark_completed() method."""
        assert lesson_progress_started.is_completed is False
        assert lesson_progress_started.completed_at is None
        
        lesson_progress_started.mark_completed()
        
        assert lesson_progress_started.is_completed is True
        assert lesson_progress_started.completion_percentage == Decimal('100.00')
        assert lesson_progress_started.completed_at is not None
    
    def test_add_time_spent(self, lesson_progress_started):
        """Test add_time_spent() method."""
        initial_time = lesson_progress_started.time_spent_seconds
        
        lesson_progress_started.add_time_spent(300)
        
        assert lesson_progress_started.time_spent_seconds == initial_time + 300
    
    def test_increment_view_count(self, lesson_progress_started):
        """Test increment_view_count() method."""
        initial_count = lesson_progress_started.view_count
        
        lesson_progress_started.increment_view_count()
        
        assert lesson_progress_started.view_count == initial_count + 1
    
    def test_completed_lesson_progress(self, lesson_progress_completed):
        """Test completed lesson progress."""
        assert lesson_progress_completed.is_completed is True
        assert lesson_progress_completed.completion_percentage == Decimal('100.00')
        assert lesson_progress_completed.completed_at is not None
    
    def test_unique_student_module(self, lesson_progress_started):
        """Test student + module must be unique."""
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                LessonProgress.objects.create(
                    student=lesson_progress_started.student,
                    module=lesson_progress_started.module,
                    completion_percentage=Decimal('50.00')
                )


# ============================================================================
# LEARNING PATH PROGRESS MODEL TESTS
# ============================================================================

@pytest.mark.django_db
class TestLearningPathProgressModel:
    """Test LearningPathProgress model."""
    
    def test_create_path_progress(self, path_progress_in_progress):
        """Test creating path progress."""
        assert path_progress_in_progress.completion_percentage == Decimal('45.00')
        assert path_progress_in_progress.status == 'in_progress'
        assert path_progress_in_progress.is_unlocked is True
    
    def test_path_progress_str_representation(self, path_progress_in_progress, student_user, course_path):
        """Test __str__ method."""
        str_repr = str(path_progress_in_progress)
        assert student_user.name in str_repr
        assert course_path.label in str_repr
        assert '45' in str_repr
    
    def test_calculate_completion(self, student_user, course_path, module, module_2):
        """Test calculate_completion() method."""
        # Create path progress
        path_progress = LearningPathProgress.objects.create(
            student=student_user,
            path=course_path
        )
        
        # Create lesson progress for both modules
        LessonProgress.objects.create(
            student=student_user,
            module=module,
            completion_percentage=Decimal('100.00'),
            is_completed=True
        )
        
        LessonProgress.objects.create(
            student=student_user,
            module=module_2,
            completion_percentage=Decimal('50.00'),
            is_completed=False
        )
        
        # Calculate completion (1 of 2 modules completed = 50%)
        completion = path_progress.calculate_completion()
        assert completion == Decimal('50.00')
    
    def test_update_completion(self, student_user, course_path, module):
        """Test update_completion() method."""
        path_progress = LearningPathProgress.objects.create(
            student=student_user,
            path=course_path,
            completion_percentage=Decimal('0.00'),
            status='not_started'
        )
        
        # Complete the module
        LessonProgress.objects.create(
            student=student_user,
            module=module,
            completion_percentage=Decimal('100.00'),
            is_completed=True
        )
        
        path_progress.update_completion()
        
        assert path_progress.completion_percentage == Decimal('100.00')
        assert path_progress.status == 'completed'
        assert path_progress.completed_at is not None
    
    def test_unlock_path(self, path_progress_locked):
        """Test unlock() method."""
        assert path_progress_locked.is_unlocked is False
        assert path_progress_locked.unlocked_at is None
        
        path_progress_locked.unlock()
        
        assert path_progress_locked.is_unlocked is True
        assert path_progress_locked.unlocked_at is not None
    
    def test_completed_path_progress(self, path_progress_completed):
        """Test completed path progress."""
        assert path_progress_completed.status == 'completed'
        assert path_progress_completed.completion_percentage == Decimal('100.00')
        assert path_progress_completed.completed_at is not None
    
    def test_unique_student_path(self, path_progress_in_progress):
        """Test student + path must be unique."""
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                LearningPathProgress.objects.create(
                    student=path_progress_in_progress.student,
                    path=path_progress_in_progress.path
                )


# ============================================================================
# QUIZ ATTEMPT SUMMARY MODEL TESTS
# ============================================================================

@pytest.mark.django_db
class TestQuizAttemptSummaryModel:
    """Test QuizAttemptSummary model."""
    
    def test_create_quiz_summary(self, quiz_summary_passed):
        """Test creating quiz summary."""
        assert quiz_summary_passed.best_score == 85
        assert quiz_summary_passed.last_score == 85
        assert quiz_summary_passed.total_attempts == 2
        assert quiz_summary_passed.has_passed is True
    
    def test_quiz_summary_str_representation(self, quiz_summary_passed, student_user):
        """Test __str__ method."""
        str_repr = str(quiz_summary_passed)
        assert student_user.name in str_repr
        assert 'Best: 85' in str_repr
    
    def test_update_from_attempt(self, student_user, quiz, quiz_attempt_passed):
        """Test update_from_attempt() method."""
        summary = QuizAttemptSummary.objects.create(
            student=student_user,
            quiz=quiz,
            best_score=0,
            last_score=0,
            total_attempts=0
        )
        
        summary.update_from_attempt(quiz_attempt_passed)
        
        assert summary.best_score == 85
        assert summary.last_score == 85
        assert summary.total_attempts == 1
        assert summary.has_passed is True
        assert summary.last_attempt_at is not None
    
    def test_failed_quiz_summary(self, quiz_summary_failed):
        """Test quiz summary with failing scores."""
        assert quiz_summary_failed.has_passed is False
        assert quiz_summary_failed.best_score == 60
        assert quiz_summary_failed.passed_attempts == 0
    
    def test_unique_student_quiz(self, quiz_summary_passed):
        """Test student + quiz must be unique."""
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                QuizAttemptSummary.objects.create(
                    student=quiz_summary_passed.student,
                    quiz=quiz_summary_passed.quiz
                )


# ============================================================================
# FLASHCARD SET PROGRESS MODEL TESTS
# ============================================================================

@pytest.mark.django_db
class TestFlashcardSetProgressModel:
    """Test FlashcardSetProgress model."""
    
    def test_create_flashcard_set_progress(self, flashcard_set_progress_partial):
        """Test creating flashcard set progress."""
        assert flashcard_set_progress_partial.total_cards == 10
        assert flashcard_set_progress_partial.mastered_cards == 4
        assert flashcard_set_progress_partial.mastery_percentage == Decimal('40.00')
        assert flashcard_set_progress_partial.is_fully_mastered is False
    
    def test_flashcard_set_progress_str_representation(self, flashcard_set_progress_partial, student_user, module):
        """Test __str__ method."""
        str_repr = str(flashcard_set_progress_partial)
        assert student_user.name in str_repr
        assert module.title in str_repr
        assert '4/10' in str_repr
    
    def test_calculate_progress(self, student_user, module, flashcard, flashcard_progress_mastered):
        """Test calculate_progress() method."""
        progress = FlashcardSetProgress.objects.create(
            student=student_user,
            module=module
        )
        
        # Calculate progress
        result = progress.calculate_progress()
        
        assert progress.total_cards == 1
        assert progress.mastered_cards == 1
        assert progress.mastery_percentage == Decimal('100.00')
        assert progress.is_fully_mastered is True
    
    def test_fully_mastered_flashcard_set(self, flashcard_set_progress_mastered):
        """Test fully mastered flashcard set."""
        assert flashcard_set_progress_mastered.is_fully_mastered is True
        assert flashcard_set_progress_mastered.mastery_percentage == Decimal('100.00')
        assert flashcard_set_progress_mastered.mastered_cards == flashcard_set_progress_mastered.total_cards
    
    def test_unique_student_module(self, flashcard_set_progress_partial):
        """Test student + module must be unique."""
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                FlashcardSetProgress.objects.create(
                    student=flashcard_set_progress_partial.student,
                    module=flashcard_set_progress_partial.module
                )


# ============================================================================
# ASSIGNMENT PROGRESS MODEL TESTS
# ============================================================================

@pytest.mark.django_db
class TestAssignmentProgressModel:
    """Test AssignmentProgress model."""
    
    def test_create_assignment_progress(self, assignment_progress_not_submitted):
        """Test creating assignment progress."""
        assert assignment_progress_not_submitted.status == 'not_submitted'
        assert assignment_progress_not_submitted.grade is None
    
    def test_assignment_progress_str_representation(self, assignment_progress_graded, student_user_2):
        """Test __str__ method."""
        str_repr = str(assignment_progress_graded)
        assert student_user_2.name in str_repr
        assert 'graded' in str_repr
    
    def test_update_from_submission(self, student_user, assignment, assignment_submission_graded):
        """Test update_from_submission() method."""
        progress = AssignmentProgress.objects.create(
            student=student_user,
            assignment=assignment,
            status='not_submitted'
        )
        
        progress.update_from_submission(assignment_submission_graded)
        
        assert progress.status == 'graded'
        assert progress.grade == 88
        assert progress.feedback == "Good work!"
        assert progress.graded_at is not None
    
    def test_graded_assignment_progress(self, assignment_progress_graded):
        """Test graded assignment progress."""
        assert assignment_progress_graded.status == 'graded'
        assert assignment_progress_graded.grade == 88
        assert assignment_progress_graded.feedback != ""
        assert assignment_progress_graded.is_late is False
    
    def test_unique_student_assignment(self, assignment_progress_not_submitted):
        """Test student + assignment must be unique."""
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                AssignmentProgress.objects.create(
                    student=assignment_progress_not_submitted.student,
                    assignment=assignment_progress_not_submitted.assignment
                )


# ============================================================================
# CHAT SESSION METRIC MODEL TESTS
# ============================================================================

@pytest.mark.django_db
class TestChatSessionMetricModel:
    """Test ChatSessionMetric model."""
    
    def test_create_chat_metric(self, chat_metric):
        """Test creating chat session metric."""
        assert chat_metric.total_sessions == 2
        assert chat_metric.total_messages == 15
        assert chat_metric.total_time_seconds == 900
    
    def test_chat_metric_str_representation(self, chat_metric, student_user, module):
        """Test __str__ method."""
        str_repr = str(chat_metric)
        assert student_user.name in str_repr
        assert module.title in str_repr
        assert '15 msgs' in str_repr
    
    def test_calculate_metrics(self, student_user, module, chat_session):
        """Test calculate_metrics() method."""
        metric = ChatSessionMetric.objects.create(
            student=student_user,
            module=module
        )
        
        result = metric.calculate_metrics()
        
        assert metric.total_sessions == 1
        assert metric.total_messages == 5
        assert metric.total_time_seconds == 600
        assert result['total_messages'] == 5
    
    def test_unique_student_module(self, chat_metric):
        """Test student + module must be unique."""
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                ChatSessionMetric.objects.create(
                    student=chat_metric.student,
                    module=chat_metric.module
                )


# ============================================================================
# TOPIC ANALYTICS MODEL TESTS
# ============================================================================

@pytest.mark.django_db
class TestTopicAnalyticsModel:
    """Test TopicAnalytics model."""
    
    def test_create_topic_analytics(self, topic_analytics_weak):
        """Test creating topic analytics."""
        assert topic_analytics_weak.topic_name == 'Programming Basics'
        assert topic_analytics_weak.strength_score == Decimal('35.00')
        assert topic_analytics_weak.strength_level == 'weak'
    
    def test_topic_analytics_str_representation(self, topic_analytics_weak, student_user):
        """Test __str__ method."""
        str_repr = str(topic_analytics_weak)
        assert student_user.name in str_repr
        assert 'Programming Basics' in str_repr
        assert '35' in str_repr
    
    def test_calculate_strength_level(self, student_user, course):
        """Test calculate_strength_level() method."""
        # Test weak (0-40)
        weak = TopicAnalytics.objects.create(
            student=student_user,
            course=course,
            topic_name='Topic A',
            strength_score=Decimal('35.00')
        )
        weak.calculate_strength_level()
        assert weak.strength_level == 'weak'
        
        # Test developing (41-60)
        developing = TopicAnalytics.objects.create(
            student=student_user,
            course=course,
            topic_name='Topic B',
            strength_score=Decimal('55.00')
        )
        developing.calculate_strength_level()
        assert developing.strength_level == 'developing'
        
        # Test proficient (61-80)
        proficient = TopicAnalytics.objects.create(
            student=student_user,
            course=course,
            topic_name='Topic C',
            strength_score=Decimal('75.00')
        )
        proficient.calculate_strength_level()
        assert proficient.strength_level == 'proficient'
        
        # Test strong (81-100)
        strong = TopicAnalytics.objects.create(
            student=student_user,
            course=course,
            topic_name='Topic D',
            strength_score=Decimal('90.00')
        )
        strong.calculate_strength_level()
        assert strong.strength_level == 'strong'
    
    def test_is_weak_topic(self, topic_analytics_weak):
        """Test is_weak_topic() method."""
        assert topic_analytics_weak.is_weak_topic() is True
    
    def test_is_not_weak_topic(self, topic_analytics_strong):
        """Test strong topic is not weak."""
        assert topic_analytics_strong.is_weak_topic() is False
    
    def test_strong_topic_analytics(self, topic_analytics_strong):
        """Test strong topic analytics."""
        assert topic_analytics_strong.strength_level == 'strong'
        assert topic_analytics_strong.strength_score >= Decimal('81.00')
    
    def test_unique_student_course_topic(self, topic_analytics_weak):
        """Test student + course + topic_name must be unique."""
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                TopicAnalytics.objects.create(
                    student=topic_analytics_weak.student,
                    course=topic_analytics_weak.course,
                    topic_name=topic_analytics_weak.topic_name,
                    strength_score=Decimal('50.00')
                )


# ============================================================================
# PATH REQUIREMENT MODEL TESTS
# ============================================================================

@pytest.mark.django_db
class TestPathRequirementModel:
    """Test PathRequirement model."""
    
    def test_create_quiz_requirement(self, path_requirement_quiz):
        """Test creating quiz requirement."""
        assert path_requirement_quiz.requirement_type == 'quiz'
        assert path_requirement_quiz.minimum_score == 70
        assert path_requirement_quiz.is_mandatory is True
    
    def test_create_assignment_requirement(self, path_requirement_assignment):
        """Test creating assignment requirement."""
        assert path_requirement_assignment.requirement_type == 'assignment'
        assert path_requirement_assignment.minimum_score == 75
    
    def test_create_flashcard_requirement(self, path_requirement_flashcard):
        """Test creating flashcard requirement."""
        assert path_requirement_flashcard.requirement_type == 'flashcard'
        assert path_requirement_flashcard.minimum_mastery == 80
        assert path_requirement_flashcard.is_mandatory is False
    
    def test_create_chat_requirement(self, path_requirement_chat):
        """Test creating chat requirement."""
        assert path_requirement_chat.requirement_type == 'chat'
        assert path_requirement_chat.minimum_messages == 10
    
    def test_requirement_str_representation(self, path_requirement_quiz):
        """Test __str__ method."""
        str_repr = str(path_requirement_quiz)
        assert 'Quiz' in str_repr
    
    def test_get_description(self, path_requirement_quiz):
        """Test get_description() method."""
        description = path_requirement_quiz.get_description()
        assert 'Score at least 70%' in description
        assert path_requirement_quiz.target_quiz.title in description


# ============================================================================
# PATH REQUIREMENT STATE MODEL TESTS
# ============================================================================

@pytest.mark.django_db
class TestPathRequirementStateModel:
    """Test PathRequirementState model."""
    
    def test_create_requirement_state(self, requirement_state_not_started):
        """Test creating requirement state."""
        assert requirement_state_not_started.state == 'not_started'
        assert requirement_state_not_started.progress_percentage == Decimal('0.00')
    
    def test_requirement_state_str_representation(self, requirement_state_completed, student_user):
        """Test __str__ method."""
        str_repr = str(requirement_state_completed)
        assert student_user.name in str_repr
        assert 'completed' in str_repr
    
    def test_check_completion_quiz(self, student_user, path_requirement_quiz, quiz, quiz_summary_passed):
        """Test check_completion() for quiz requirement."""
        state = PathRequirementState.objects.create(
            student=student_user,
            requirement=path_requirement_quiz
        )
        
        is_complete = state.check_completion()
        
        assert is_complete is True
        assert state.state == 'completed'
        assert state.progress_percentage == Decimal('100.00')
    
    def test_check_completion_assignment(self, student_user_2, path_requirement_assignment, assignment_progress_graded):
        """Test check_completion() for assignment requirement."""
        state = PathRequirementState.objects.create(
            student=student_user_2,
            requirement=path_requirement_assignment
        )
        
        is_complete = state.check_completion()
        
        assert is_complete is True
        assert state.state == 'completed'
    
    def test_is_completed(self, requirement_state_completed):
        """Test is_completed() method."""
        assert requirement_state_completed.is_completed() is True
    
    def test_is_not_completed(self, requirement_state_not_started):
        """Test requirement not completed."""
        assert requirement_state_not_started.is_completed() is False
    
    def test_in_progress_state(self, requirement_state_in_progress):
        """Test in-progress requirement state."""
        assert requirement_state_in_progress.state == 'in_progress'
        assert Decimal('0.00') < requirement_state_in_progress.progress_percentage < Decimal('100.00')
    
    def test_unique_student_requirement(self, requirement_state_completed):
        """Test student + requirement must be unique."""
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                PathRequirementState.objects.create(
                    student=requirement_state_completed.student,
                    requirement=requirement_state_completed.requirement
                )


# ============================================================================
# MANAGER TESTS
# ============================================================================

@pytest.mark.django_db
class TestProgressManagers:
    """Test custom managers for progress models."""
    
    def test_lesson_progress_completed_manager(self, lesson_progress_completed, lesson_progress_started):
        """Test LessonProgress completed() manager."""
        completed = LessonProgress.objects.completed()
        
        assert lesson_progress_completed in completed
        assert lesson_progress_started not in completed
    
    def test_lesson_progress_in_progress_manager(self, lesson_progress_started, lesson_progress_completed):
        """Test LessonProgress in_progress() manager."""
        in_progress = LessonProgress.objects.in_progress()
        
        assert lesson_progress_started in in_progress
        assert lesson_progress_completed not in in_progress
    
    def test_path_progress_unlocked_manager(self, path_progress_in_progress, path_progress_locked):
        """Test LearningPathProgress unlocked() manager."""
        unlocked = LearningPathProgress.objects.unlocked()
        
        assert path_progress_in_progress in unlocked
        assert path_progress_locked not in unlocked
    
    def test_quiz_summary_passed_manager(self, quiz_summary_passed, quiz_summary_failed):
        """Test QuizAttemptSummary passed() manager."""
        passed = QuizAttemptSummary.objects.passed()
        
        assert quiz_summary_passed in passed
        assert quiz_summary_failed not in passed
    
    def test_flashcard_set_fully_mastered_manager(self, flashcard_set_progress_mastered, flashcard_set_progress_partial):
        """Test FlashcardSetProgress fully_mastered() manager."""
        mastered = FlashcardSetProgress.objects.fully_mastered()
        
        assert flashcard_set_progress_mastered in mastered
        assert flashcard_set_progress_partial not in mastered
    
    def test_topic_analytics_weak_topics_manager(self, topic_analytics_weak, topic_analytics_strong):
        """Test TopicAnalytics weak_topics() manager."""
        weak = TopicAnalytics.objects.weak_topics()
        
        assert topic_analytics_weak in weak
        assert topic_analytics_strong not in weak
    
    def test_path_requirement_mandatory_manager(self, path_requirement_quiz, path_requirement_flashcard):
        """Test PathRequirement mandatory() manager."""
        mandatory = PathRequirement.objects.mandatory()
        
        assert path_requirement_quiz in mandatory
        assert path_requirement_flashcard not in mandatory
    
    def test_requirement_state_completed_manager(self, requirement_state_completed, requirement_state_not_started):
        """Test PathRequirementState completed() manager."""
        completed = PathRequirementState.objects.completed()
        
        assert requirement_state_completed in completed
        assert requirement_state_not_started not in completed