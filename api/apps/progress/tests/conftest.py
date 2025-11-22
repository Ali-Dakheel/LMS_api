"""
Pytest fixtures for progress app tests.

Imports fixtures from root conftest and adds progress-specific fixtures.
"""

import pytest
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
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

User = get_user_model()

# NOTE: Root conftest.py provides these fixtures automatically:
# - academic_year, program, cohort, term_sem1, term_sem2
# - subject, course, class_section_university
# - course_offering, enrollment
# - student_user, student_user_2, teacher_user, dean_user, admin_user
# - university_setup, k12_setup


# ============================================================================
# COURSES APP FIXTURES (if not already in root)
# ============================================================================

@pytest.fixture
def course_path(course, teacher_user):
    """Create a CoursePath for testing."""
    from apps.courses.models import CoursePath
    
    return CoursePath.objects.create(
        course=course,
        scope='course',
        label='Week 1: Introduction to Data Structures',
        slug='week-1-intro',
        description='Introduction to fundamental data structures',
        objectives='- Understand basic data structure concepts\n- Learn about arrays and lists',
        outcomes='- CILO 1: Demonstrate understanding of arrays\n- CILO 2: Implement basic list operations',
        start_date=timezone.now().date(),
        end_date=(timezone.now() + timedelta(days=7)).date(),
        source_kind='manual',
        generation_status='complete',
        is_published=True,
        published_at=timezone.now(),
        order=1
    )


@pytest.fixture
def course_path_2(course, teacher_user):
    """Create second CoursePath for sequential testing."""
    from apps.courses.models import CoursePath
    
    return CoursePath.objects.create(
        course=course,
        scope='course',
        label='Week 2: Advanced Topics',
        slug='week-2-advanced',
        description='Advanced data structure topics',
        start_date=(timezone.now() + timedelta(days=7)).date(),
        end_date=(timezone.now() + timedelta(days=14)).date(),
        source_kind='manual',
        generation_status='complete',
        is_published=True,
        published_at=timezone.now(),
        order=2
    )


@pytest.fixture
def module(course_path, teacher_user):
    """Create PathModule for testing."""
    from apps.courses.models import PathModule
    
    return PathModule.objects.create(
        path=course_path,
        title='Variables and Expressions',
        slug='variables-expressions',
        category='Programming Basics',
        description='Learn about variables and expressions in programming',
        outcomes='- Understand variable declaration\n- Use expressions correctly',
        order=1,
        is_published=True,
        published_at=timezone.now()
    )


@pytest.fixture
def module_2(course_path, teacher_user):
    """Create second PathModule for testing."""
    from apps.courses.models import PathModule
    
    return PathModule.objects.create(
        path=course_path,
        title='Control Structures',
        slug='control-structures',
        category='Programming Basics',
        description='Learn about if statements and loops',
        order=2,
        is_published=True,
        published_at=timezone.now()
    )


# ============================================================================
# ASSESSMENTS APP FIXTURES
# ============================================================================

@pytest.fixture
def quiz(module, teacher_user):
    """Create a quiz for testing."""
    from apps.assessments.models import Quiz
    
    return Quiz.objects.create(
        module=module,
        title="Variables Quiz",
        description="Test your knowledge of variables.",
        difficulty='medium',
        duration_minutes=30,
        passing_score=70,
        is_published=True,
        created_by=teacher_user
    )


@pytest.fixture
def quiz_attempt_passed(quiz, student_user):
    """Create a passed quiz attempt."""
    from apps.assessments.models import QuizAttempt
    
    return QuizAttempt.objects.create(
        quiz=quiz,
        student=student_user,
        attempt_number=1,
        status='submitted',
        score=85,
        total_points_earned=8,
        total_points_possible=10,
        passed=True,
        started_at=timezone.now() - timedelta(minutes=25),
        submitted_at=timezone.now(),
        time_taken_seconds=1500
    )


@pytest.fixture
def assignment(module, teacher_user):
    """Create an assignment for testing."""
    from apps.assessments.models import Assignment
    
    return Assignment.objects.create(
        module=module,
        title="Week 1 Assignment: Variables",
        description="<p>Complete exercises on variables.</p>",
        due_date=timezone.now() + timedelta(days=7),
        weight=100,
        max_score=100,
        is_published=True,
        created_by=teacher_user
    )


@pytest.fixture
def assignment_submission_graded(assignment, student_user, teacher_user):
    """Create a graded assignment submission."""
    from apps.assessments.models import AssignmentSubmission
    
    return AssignmentSubmission.objects.create(
        assignment=assignment,
        student=student_user,
        content="My completed assignment.",
        status='graded',
        grade=88,
        feedback="Good work!",
        graded_by=teacher_user,
        submitted_at=timezone.now() - timedelta(days=2),
        graded_at=timezone.now() - timedelta(days=1)
    )


@pytest.fixture
def flashcard(module, teacher_user):
    """Create a flashcard for testing."""
    from apps.assessments.models import Flashcard
    
    return Flashcard.objects.create(
        module=module,
        question="What is a variable?",
        answer="A container for storing data values.",
        order=0,
        is_active=True,
        created_by=teacher_user
    )


@pytest.fixture
def flashcard_progress_mastered(flashcard, student_user):
    """Create mastered flashcard progress."""
    from apps.assessments.models import FlashcardProgress
    
    return FlashcardProgress.objects.create(
        flashcard=flashcard,
        student=student_user,
        ease_factor=2.5,
        interval_days=30,
        repetitions=5,
        last_reviewed_at=timezone.now() - timedelta(days=29),
        next_review_at=timezone.now() + timedelta(days=1),
        total_reviews=7,
        correct_reviews=6,
        is_mastered=True
    )


# ============================================================================
# COMMUNICATIONS APP FIXTURES
# ============================================================================

@pytest.fixture
def chat_session(student_user, module):
    """Create a chat session for testing."""
    from apps.communications.models import ChatSession
    
    return ChatSession.objects.create(
        student=student_user,
        module=module,
        title="How do variables work?",
        status='active',
        total_messages=5,
        total_time_seconds=600,
        last_message_at=timezone.now()
    )


# ============================================================================
# LESSON PROGRESS FIXTURES
# ============================================================================

@pytest.fixture
def lesson_progress_started(student_user, module):
    """Create a started but not completed lesson progress."""
    return LessonProgress.objects.create(
        student=student_user,
        module=module,
        completion_percentage=Decimal('45.00'),
        is_completed=False,
        time_spent_seconds=900,
        view_count=3
    )


@pytest.fixture
def lesson_progress_completed(student_user_2, module):
    """Create a completed lesson progress."""
    return LessonProgress.objects.create(
        student=student_user_2,
        module=module,
        completion_percentage=Decimal('100.00'),
        is_completed=True,
        completed_at=timezone.now() - timedelta(days=1),
        time_spent_seconds=1800,
        view_count=5
    )


@pytest.fixture
def multiple_lesson_progress(student_user, module, module_2):
    """Create multiple lesson progress records."""
    progress_list = []
    
    # Module 1: Completed
    p1 = LessonProgress.objects.create(
        student=student_user,
        module=module,
        completion_percentage=Decimal('100.00'),
        is_completed=True,
        completed_at=timezone.now() - timedelta(days=2),
        time_spent_seconds=1500,
        view_count=4
    )
    progress_list.append(p1)
    
    # Module 2: In progress
    p2 = LessonProgress.objects.create(
        student=student_user,
        module=module_2,
        completion_percentage=Decimal('60.00'),
        is_completed=False,
        time_spent_seconds=800,
        view_count=2
    )
    progress_list.append(p2)
    
    return progress_list


# ============================================================================
# LEARNING PATH PROGRESS FIXTURES
# ============================================================================

@pytest.fixture
def path_progress_in_progress(student_user, course_path):
    """Create in-progress path progress."""
    return LearningPathProgress.objects.create(
        student=student_user,
        path=course_path,
        completion_percentage=Decimal('45.00'),
        status='in_progress',
        last_step_key='variables-expressions',
        progress_index=1,
        is_unlocked=True
    )


@pytest.fixture
def path_progress_completed(student_user_2, course_path):
    """Create completed path progress."""
    return LearningPathProgress.objects.create(
        student=student_user_2,
        path=course_path,
        completion_percentage=Decimal('100.00'),
        status='completed',
        completed_at=timezone.now() - timedelta(days=1),
        is_unlocked=True
    )


@pytest.fixture
def path_progress_locked(student_user, course_path_2):
    """Create locked path progress."""
    return LearningPathProgress.objects.create(
        student=student_user,
        path=course_path_2,
        completion_percentage=Decimal('0.00'),
        status='locked',
        is_unlocked=False
    )


# ============================================================================
# QUIZ ATTEMPT SUMMARY FIXTURES
# ============================================================================

@pytest.fixture
def quiz_summary_passed(student_user, quiz):
    """Create quiz summary with passing score."""
    return QuizAttemptSummary.objects.create(
        student=student_user,
        quiz=quiz,
        best_score=85,
        last_score=85,
        average_score=Decimal('82.50'),
        total_attempts=2,
        passed_attempts=2,
        has_passed=True,
        average_time_seconds=1400,
        first_attempt_at=timezone.now() - timedelta(days=3),
        last_attempt_at=timezone.now() - timedelta(days=1)
    )


@pytest.fixture
def quiz_summary_failed(student_user_2, quiz):
    """Create quiz summary with failing score."""
    return QuizAttemptSummary.objects.create(
        student=student_user_2,
        quiz=quiz,
        best_score=60,
        last_score=55,
        average_score=Decimal('57.50'),
        total_attempts=2,
        passed_attempts=0,
        has_passed=False,
        first_attempt_at=timezone.now() - timedelta(days=2),
        last_attempt_at=timezone.now()
    )


# ============================================================================
# FLASHCARD SET PROGRESS FIXTURES
# ============================================================================

@pytest.fixture
def flashcard_set_progress_partial(student_user, module):
    """Create partially mastered flashcard set progress."""
    return FlashcardSetProgress.objects.create(
        student=student_user,
        module=module,
        total_cards=10,
        mastered_cards=4,
        mastery_percentage=Decimal('40.00'),
        cards_due_today=2,
        next_review_at=timezone.now() + timedelta(hours=6),
        is_fully_mastered=False
    )


@pytest.fixture
def flashcard_set_progress_mastered(student_user_2, module):
    """Create fully mastered flashcard set progress."""
    return FlashcardSetProgress.objects.create(
        student=student_user_2,
        module=module,
        total_cards=10,
        mastered_cards=10,
        mastery_percentage=Decimal('100.00'),
        cards_due_today=0,
        is_fully_mastered=True
    )


# ============================================================================
# ASSIGNMENT PROGRESS FIXTURES
# ============================================================================

@pytest.fixture
def assignment_progress_not_submitted(student_user, assignment):
    """Create not-submitted assignment progress."""
    return AssignmentProgress.objects.create(
        student=student_user,
        assignment=assignment,
        status='not_submitted'
    )


@pytest.fixture
def assignment_progress_graded(student_user_2, assignment):
    """Create graded assignment progress."""
    return AssignmentProgress.objects.create(
        student=student_user_2,
        assignment=assignment,
        status='graded',
        grade=88,
        feedback="Well done!",
        submitted_at=timezone.now() - timedelta(days=2),
        graded_at=timezone.now() - timedelta(days=1),
        is_late=False
    )


# ============================================================================
# CHAT SESSION METRIC FIXTURES
# ============================================================================

@pytest.fixture
def chat_metric(student_user, module):
    """Create chat session metric."""
    return ChatSessionMetric.objects.create(
        student=student_user,
        module=module,
        total_sessions=2,
        active_sessions=1,
        completed_sessions=1,
        total_messages=15,
        total_time_seconds=900,
        last_chat_at=timezone.now()
    )


# ============================================================================
# TOPIC ANALYTICS FIXTURES
# ============================================================================

@pytest.fixture
def topic_analytics_weak(student_user, course):
    """Create weak topic analytics."""
    return TopicAnalytics.objects.create(
        student=student_user,
        course=course,
        topic_name='Programming Basics',
        strength_score=Decimal('35.00'),
        strength_level='weak',
        quiz_average=Decimal('40.00'),
        assignment_average=Decimal('30.00'),
        flashcard_mastery=Decimal('35.00'),
        ai_insights="Needs more practice with basic concepts."
    )


@pytest.fixture
def topic_analytics_strong(student_user_2, course):
    """Create strong topic analytics."""
    return TopicAnalytics.objects.create(
        student=student_user_2,
        course=course,
        topic_name='Programming Basics',
        strength_score=Decimal('90.00'),
        strength_level='strong',
        quiz_average=Decimal('95.00'),
        assignment_average=Decimal('88.00'),
        flashcard_mastery=Decimal('87.00'),
        ai_insights="Excellent understanding of fundamentals."
    )


# ============================================================================
# PATH REQUIREMENT FIXTURES
# ============================================================================

@pytest.fixture
def path_requirement_quiz(course_path, quiz):
    """Create quiz requirement for path."""
    return PathRequirement.objects.create(
        path=course_path,
        requirement_type='quiz',
        target_quiz=quiz,
        minimum_score=70,
        weight=2,
        is_mandatory=True,
        order=1
    )


@pytest.fixture
def path_requirement_assignment(course_path, assignment):
    """Create assignment requirement for path."""
    return PathRequirement.objects.create(
        path=course_path,
        requirement_type='assignment',
        target_assignment=assignment,
        minimum_score=75,
        weight=2,
        is_mandatory=True,
        order=2
    )


@pytest.fixture
def path_requirement_flashcard(course_path, module):
    """Create flashcard requirement for path."""
    return PathRequirement.objects.create(
        path=course_path,
        requirement_type='flashcard',
        target_module=module,
        minimum_mastery=80,
        weight=1,
        is_mandatory=False,
        order=3
    )


@pytest.fixture
def path_requirement_chat(course_path, module):
    """Create chat requirement for path."""
    return PathRequirement.objects.create(
        path=course_path,
        requirement_type='chat',
        target_module=module,
        minimum_messages=10,
        weight=1,
        is_mandatory=False,
        order=4
    )


# ============================================================================
# PATH REQUIREMENT STATE FIXTURES
# ============================================================================

@pytest.fixture
def requirement_state_completed(student_user, path_requirement_quiz):
    """Create completed requirement state."""
    return PathRequirementState.objects.create(
        student=student_user,
        requirement=path_requirement_quiz,
        state='completed',
        progress_percentage=Decimal('100.00'),
        current_score=85,
        attempt_count=2,
        completed_at=timezone.now() - timedelta(days=1),
        last_event_at=timezone.now() - timedelta(days=1)
    )


@pytest.fixture
def requirement_state_in_progress(student_user, path_requirement_assignment):
    """Create in-progress requirement state."""
    return PathRequirementState.objects.create(
        student=student_user,
        requirement=path_requirement_assignment,
        state='in_progress',
        progress_percentage=Decimal('60.00'),
        current_score=60,
        attempt_count=1,
        last_event_at=timezone.now()
    )


@pytest.fixture
def requirement_state_not_started(student_user, path_requirement_flashcard):
    """Create not-started requirement state."""
    return PathRequirementState.objects.create(
        student=student_user,
        requirement=path_requirement_flashcard,
        state='not_started',
        progress_percentage=Decimal('0.00'),
        attempt_count=0
    )