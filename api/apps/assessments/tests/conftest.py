"""
Pytest fixtures for assessments app tests.

Imports fixtures from root conftest and adds assessment-specific fixtures.
"""

import pytest
from datetime import timedelta
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.assessments.models import (
    Assignment,
    AssignmentSubmission,
    AssignmentAttachment,
    SubmissionAttachment,
    Quiz,
    QuizQuestion,
    QuizAttempt,
    QuizAttemptAnswer,
    Flashcard,
    FlashcardProgress,
    Worksheet,
)

User = get_user_model()

# NOTE: Root conftest.py provides these fixtures automatically:
# - academic_year, program, cohort, term_sem1, term_sem2
# - subject, course, class_section_university
# - course_offering, enrollment
# - student_user, student_user_2, teacher_user, dean_user, admin_user
# - university_setup, k12_setup


# ============================================================================
# COURSES APP FIXTURES
# ============================================================================

@pytest.fixture
def course_path(course, teacher_user):
    """
    Create a CoursePath for testing.
    
    Uses the correct model name: CoursePath (not LearningPath)
    """
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
def module(course_path, teacher_user):
    """
    Create PathModule for testing.
    
    Depends on course_path fixture.
    """
    from apps.courses.models import PathModule
    
    return PathModule.objects.create(
        path=course_path,
        title='Variables and Expressions',
        slug='variables-expressions',
        category='lesson',
        description='Learn about variables and expressions in programming',
        outcomes='- Understand variable declaration\n- Use expressions correctly',
        order=1,
        is_published=True,
        published_at=timezone.now()
    )


@pytest.fixture
def module_detail(module):
    """Create ModuleDetail with rich text content."""
    from apps.courses.models import ModuleDetail
    
    return ModuleDetail.objects.create(
        module=module,
        content_type='text',
        text_content='<h2>Variables</h2><p>A variable is a container for storing data values.</p>',
        objectives='- Define variables\n- Use variables in expressions',
        is_ai_generated=False
    )


# ============================================================================
# HELPER FIXTURES
# ============================================================================

@pytest.fixture
def dummy_pdf_file():
    """Create a dummy PDF file."""
    pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
xref
0 2
trailer
<<
/Size 2
/Root 1 0 R
>>
startxref
89
%%EOF"""
    
    return SimpleUploadedFile(
        name='assignment.pdf',
        content=pdf_content,
        content_type='application/pdf'
    )


@pytest.fixture
def dummy_image():
    """Create a dummy image file."""
    png_content = (
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
        b'\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00'
        b'\x00\x0cIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4'
        b'\x00\x00\x00\x00IEND\xaeB`\x82'
    )
    return SimpleUploadedFile(
        name='test.png',
        content=png_content,
        content_type='image/png'
    )


# ============================================================================
# ASSIGNMENT FIXTURES
# ============================================================================

@pytest.fixture
def assignment(module, teacher_user):
    """Create a published assignment."""
    return Assignment.objects.create(
        module=module,
        title="Week 1 Assignment: Variables",
        description="<p>Complete exercises on variables and expressions.</p>",
        due_date=timezone.now() + timedelta(days=7),
        weight=100,
        max_score=100,
        is_published=True,
        published_at=timezone.now(),
        created_by=teacher_user
    )


@pytest.fixture
def assignment_draft(module, teacher_user):
    """Create a draft assignment."""
    return Assignment.objects.create(
        module=module,
        title="Draft Assignment",
        description="<p>This is a draft.</p>",
        due_date=timezone.now() + timedelta(days=14),
        weight=50,
        max_score=50,
        is_published=False,
        created_by=teacher_user
    )


@pytest.fixture
def assignment_overdue(module, teacher_user):
    """Create an overdue assignment."""
    return Assignment.objects.create(
        module=module,
        title="Overdue Assignment",
        description="<p>This assignment is overdue.</p>",
        due_date=timezone.now() - timedelta(days=3),
        weight=100,
        max_score=100,
        is_published=True,
        published_at=timezone.now() - timedelta(days=10),
        created_by=teacher_user
    )


@pytest.fixture
def assignment_personal(module, student_user, teacher_user):
    """Create a personal assignment for specific student."""
    return Assignment.objects.create(
        module=module,
        title="Personal Remedial Assignment",
        description="<p>Extra practice for you.</p>",
        due_date=timezone.now() + timedelta(days=7),
        weight=100,
        max_score=100,
        is_published=True,
        assigned_to=student_user,
        created_by=teacher_user
    )


@pytest.fixture
def assignment_attachment(assignment, dummy_pdf_file):
    """Create assignment attachment."""
    return AssignmentAttachment.objects.create(
        assignment=assignment,
        file=dummy_pdf_file,
        title="Assignment Instructions PDF"
    )


# ============================================================================
# ASSIGNMENT SUBMISSION FIXTURES
# ============================================================================

@pytest.fixture
def submission_not_submitted(assignment, student_user):
    """Create a not-submitted submission."""
    return AssignmentSubmission.objects.create(
        assignment=assignment,
        student=student_user,
        status='not_submitted'
    )


@pytest.fixture
def submission_submitted(assignment, student_user):
    """Create a submitted submission."""
    return AssignmentSubmission.objects.create(
        assignment=assignment,
        student=student_user,
        content="My submission content goes here.",
        status='submitted',
        submitted_at=timezone.now()
    )


@pytest.fixture
def submission_graded(assignment, student_user_2, teacher_user):
    """Create a graded submission."""
    return AssignmentSubmission.objects.create(
        assignment=assignment,
        student=student_user_2,
        content="Student's completed work.",
        status='graded',
        grade=85,
        feedback="Good work! Minor improvements needed in section 3.",
        graded_by=teacher_user,
        submitted_at=timezone.now() - timedelta(days=2),
        graded_at=timezone.now() - timedelta(days=1)
    )


@pytest.fixture
def submission_attachment(submission_submitted, dummy_pdf_file):
    """Create submission attachment."""
    return SubmissionAttachment.objects.create(
        submission=submission_submitted,
        file=dummy_pdf_file,
        filename="my_submission.pdf"
    )


# ============================================================================
# QUIZ FIXTURES
# ============================================================================

@pytest.fixture
def quiz(module, teacher_user):
    """Create a published quiz."""
    return Quiz.objects.create(
        module=module,
        title="Variables Quiz",
        description="Test your knowledge of variables.",
        difficulty='medium',
        duration_minutes=30,
        passing_score=70,
        is_practice=False,
        show_answers_after=True,
        is_published=True,
        published_at=timezone.now(),
        created_by=teacher_user
    )


@pytest.fixture
def quiz_practice(module, teacher_user):
    """Create a practice quiz."""
    return Quiz.objects.create(
        module=module,
        title="Practice Quiz",
        description="Practice unlimited times.",
        difficulty='easy',
        duration_minutes=0,
        passing_score=70,
        is_practice=True,
        show_answers_after=True,
        is_published=True,
        created_by=teacher_user
    )


@pytest.fixture
def quiz_hard(module, teacher_user):
    """Create a hard quiz."""
    return Quiz.objects.create(
        module=module,
        title="Advanced Quiz",
        difficulty='hard',
        duration_minutes=60,
        passing_score=80,
        is_published=True,
        created_by=teacher_user
    )


# ============================================================================
# QUIZ QUESTION FIXTURES
# ============================================================================

@pytest.fixture
def question_mcq(quiz):
    """Create MCQ question."""
    return QuizQuestion.objects.create(
        quiz=quiz,
        question_type='mcq',
        question_text="What is a variable in programming?",
        options=[
            "A fixed value",
            "A container for storing data",
            "A function",
            "A loop"
        ],
        correct_answer="A container for storing data",
        explanation="Variables store data values that can change.",
        points=2,
        order=0
    )


@pytest.fixture
def question_fill(quiz):
    """Create fill-in-blank question."""
    return QuizQuestion.objects.create(
        quiz=quiz,
        question_type='fill',
        question_text="A variable is a _____ for storing data.",
        correct_answer="container",
        explanation="Variables are containers that hold data values.",
        points=2,
        order=1
    )


@pytest.fixture
def question_tf(quiz):
    """Create true/false question."""
    return QuizQuestion.objects.create(
        quiz=quiz,
        question_type='tf',
        question_text="Variables can change their values during program execution.",
        correct_answer="true",
        explanation="Yes, variables are mutable by design.",
        points=1,
        order=2
    )


@pytest.fixture
def question_match(quiz):
    """Create matching question."""
    return QuizQuestion.objects.create(
        quiz=quiz,
        question_type='match',
        question_text="Match the variable types with their examples:",
        matching_pairs=[
            {"left": "Integer", "right": "42"},
            {"left": "String", "right": "Hello"},
            {"left": "Boolean", "right": "True"},
            {"left": "Float", "right": "3.14"}
        ],
        correct_answer="See matching pairs",
        explanation="Each data type has specific use cases.",
        points=4,
        order=3
    )


@pytest.fixture
def complete_quiz(quiz, question_mcq, question_fill, question_tf, question_match):
    """Create a complete quiz with all question types."""
    return {
        'quiz': quiz,
        'mcq': question_mcq,
        'fill': question_fill,
        'tf': question_tf,
        'match': question_match
    }


# ============================================================================
# QUIZ ATTEMPT FIXTURES
# ============================================================================

@pytest.fixture
def quiz_attempt_in_progress(quiz, student_user):
    """Create in-progress quiz attempt."""
    return QuizAttempt.objects.create(
        quiz=quiz,
        student=student_user,
        attempt_number=1,
        status='in_progress',
        total_points_possible=9,
        started_at=timezone.now()
    )


@pytest.fixture
def quiz_attempt_submitted(quiz, student_user):
    """Create submitted quiz attempt."""
    return QuizAttempt.objects.create(
        quiz=quiz,
        student=student_user,
        attempt_number=1,
        status='submitted',
        score=85,
        total_points_earned=7,
        total_points_possible=9,
        started_at=timezone.now() - timedelta(minutes=25),
        submitted_at=timezone.now(),
        time_taken_seconds=1500,
        passed=True
    )


@pytest.fixture
def quiz_attempt_failed(quiz, student_user_2):
    """Create failed quiz attempt."""
    return QuizAttempt.objects.create(
        quiz=quiz,
        student=student_user_2,
        attempt_number=1,
        status='submitted',
        score=55,
        total_points_earned=5,
        total_points_possible=9,
        started_at=timezone.now() - timedelta(minutes=30),
        submitted_at=timezone.now(),
        time_taken_seconds=1800,
        passed=False
    )


@pytest.fixture
def quiz_attempt_answer_correct(quiz_attempt_in_progress, question_mcq):
    """Create correct answer."""
    return QuizAttemptAnswer.objects.create(
        attempt=quiz_attempt_in_progress,
        question=question_mcq,
        answer="A container for storing data",
        is_correct=True,
        points_earned=2
    )


@pytest.fixture
def quiz_attempt_answer_incorrect(quiz_attempt_in_progress, question_fill):
    """Create incorrect answer."""
    return QuizAttemptAnswer.objects.create(
        attempt=quiz_attempt_in_progress,
        question=question_fill,
        answer="box",
        is_correct=False,
        points_earned=0
    )


# ============================================================================
# FLASHCARD FIXTURES
# ============================================================================

@pytest.fixture
def flashcard(module, teacher_user):
    """Create a flashcard."""
    return Flashcard.objects.create(
        module=module,
        question="What is a variable?",
        answer="A container for storing data values.",
        hint="Think of it as a labeled box.",
        order=0,
        is_ai_generated=False,
        is_active=True,
        created_by=teacher_user
    )


@pytest.fixture
def flashcard_ai(module, teacher_user):
    """Create AI-generated flashcard."""
    return Flashcard.objects.create(
        module=module,
        question="What is an expression?",
        answer="A combination of values, variables, and operators.",
        order=1,
        is_ai_generated=True,
        is_active=True,
        created_by=teacher_user
    )


@pytest.fixture
def flashcard_inactive(module, teacher_user):
    """Create inactive flashcard."""
    return Flashcard.objects.create(
        module=module,
        question="Old question",
        answer="Old answer",
        order=2,
        is_active=False,
        created_by=teacher_user
    )


@pytest.fixture
def multiple_flashcards(module, teacher_user):
    """Create multiple flashcards for testing."""
    cards = []
    for i in range(5):
        card = Flashcard.objects.create(
            module=module,
            question=f"Question {i + 1}",
            answer=f"Answer {i + 1}",
            order=i,
            is_active=True,
            created_by=teacher_user
        )
        cards.append(card)
    return cards


# ============================================================================
# FLASHCARD PROGRESS FIXTURES
# ============================================================================

@pytest.fixture
def flashcard_progress_new(flashcard, student_user):
    """Create new flashcard progress (not reviewed yet)."""
    return FlashcardProgress.objects.create(
        flashcard=flashcard,
        student=student_user,
        ease_factor=2.5,
        interval_days=1,
        repetitions=0,
        next_review_at=timezone.now()
    )


@pytest.fixture
def flashcard_progress_learning(flashcard_ai, student_user):
    """Create flashcard progress in learning phase."""
    return FlashcardProgress.objects.create(
        flashcard=flashcard_ai,
        student=student_user,
        ease_factor=2.3,
        interval_days=6,
        repetitions=2,
        last_reviewed_at=timezone.now() - timedelta(days=5),
        next_review_at=timezone.now() + timedelta(days=1),
        total_reviews=3,
        correct_reviews=2,
        is_mastered=False
    )


@pytest.fixture
def flashcard_progress_mastered(flashcard, student_user_2):
    """Create mastered flashcard progress."""
    return FlashcardProgress.objects.create(
        flashcard=flashcard,
        student=student_user_2,
        ease_factor=2.5,
        interval_days=30,
        repetitions=5,
        last_reviewed_at=timezone.now() - timedelta(days=29),
        next_review_at=timezone.now() + timedelta(days=1),
        total_reviews=7,
        correct_reviews=6,
        is_mastered=True
    )


@pytest.fixture
def flashcard_progress_due(flashcard_ai, student_user_2):
    """Create flashcard progress due for review."""
    return FlashcardProgress.objects.create(
        flashcard=flashcard_ai,
        student=student_user_2,
        ease_factor=2.0,
        interval_days=3,
        repetitions=1,
        last_reviewed_at=timezone.now() - timedelta(days=4),
        next_review_at=timezone.now() - timedelta(days=1),
        total_reviews=2,
        correct_reviews=1,
        is_mastered=False
    )


# ============================================================================
# WORKSHEET FIXTURES
# ============================================================================

@pytest.fixture
def worksheet(module, teacher_user, dummy_pdf_file):
    """Create a worksheet."""
    return Worksheet.objects.create(
        module=module,
        title="Variables Practice Worksheet",
        description="Practice exercises on variables.",
        topic="Variables and Expressions",
        difficulty='medium',
        grade_level="Grade 5",
        worksheet_file=dummy_pdf_file,
        is_ai_generated=True,
        created_by=teacher_user
    )


@pytest.fixture
def worksheet_with_answers(module, teacher_user, dummy_pdf_file):
    """Create worksheet with answer key."""
    answer_file = SimpleUploadedFile(
        name='answers.pdf',
        content=b'%PDF-1.4\nanswer key',
        content_type='application/pdf'
    )
    
    return Worksheet.objects.create(
        module=module,
        title="Algebra Worksheet with Answers",
        topic="Basic Algebra",
        difficulty='hard',
        worksheet_file=dummy_pdf_file,
        answer_key_file=answer_file,
        is_ai_generated=True,
        created_by=teacher_user
    )