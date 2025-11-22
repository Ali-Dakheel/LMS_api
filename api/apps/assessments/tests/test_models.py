"""
Unit tests for Assessments app models.

Tests:
- Assignment creation and due dates
- Assignment submissions and grading
- Quiz creation and question types
- Quiz attempts and auto-grading
- Flashcard SRS algorithm
- Worksheet generation
"""

import pytest
from datetime import timedelta
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone

from apps.assessments.models import (
    Assignment,
    AssignmentSubmission,
    Quiz,
    QuizQuestion,
    QuizAttempt,
    QuizAttemptAnswer,
    Flashcard,
    FlashcardProgress,
    Worksheet,
)
from django.db import transaction


# ============================================================================
# ASSIGNMENT MODEL TESTS
# ============================================================================

@pytest.mark.django_db
class TestAssignmentModel:
    """Test Assignment model."""
    
    def test_create_assignment(self, assignment):
        """Test creating an assignment."""
        assert assignment.title == "Week 1 Assignment: Variables"
        assert assignment.weight == 100
        assert assignment.max_score == 100
        assert assignment.is_published is True
    
    def test_assignment_is_overdue(self, assignment_overdue):
        """Test is_overdue() method."""
        assert assignment_overdue.is_overdue() is True
    
    def test_assignment_not_overdue(self, assignment):
        """Test assignment not yet overdue."""
        assert assignment.is_overdue() is False
    
    def test_assignment_days_until_due(self, assignment):
        """Test days_until_due() calculation."""
        days = assignment.days_until_due()
        assert days >= 6  # Due in 7 days, allow for execution time
    
    def test_assignment_str_representation(self, assignment):
        """Test __str__ method."""
        assert "Variables" in str(assignment)
        assert "Week 1" in str(assignment)
    
    def test_assignment_personal(self, assignment_personal, student_user):
        """Test personal assignment for specific student."""
        assert assignment_personal.assigned_to == student_user
    
    def test_assignment_weight_validation(self, module, teacher_user):
        """Test weight must be within valid range."""
        with pytest.raises(ValidationError):
            assignment = Assignment(
                module=module,
                title="Invalid Weight",
                due_date=timezone.now() + timedelta(days=7),
                weight=0,  # Invalid (min is 1)
                max_score=100,
                created_by=teacher_user
            )
            assignment.full_clean()


# ============================================================================
# ASSIGNMENT SUBMISSION TESTS
# ============================================================================

@pytest.mark.django_db
class TestAssignmentSubmissionModel:
    """Test AssignmentSubmission model."""
    
    def test_create_submission(self, submission_submitted):
        """Test creating a submission."""
        assert submission_submitted.status == 'submitted'
        assert submission_submitted.content != ""
        assert submission_submitted.submitted_at is not None
    
    def test_submission_unique_student_assignment(self, submission_submitted):
        """Test student + assignment must be unique."""
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                AssignmentSubmission.objects.create(
                    assignment=submission_submitted.assignment,
                    student=submission_submitted.student,
                    status='not_submitted'
                )
    
    def test_submission_is_late(self, assignment_overdue, student_user):
        """Test is_late() method."""
        submission = AssignmentSubmission.objects.create(
            assignment=assignment_overdue,
            student=student_user,
            status='submitted',
            submitted_at=timezone.now()
        )
        
        assert submission.is_late() is True
    
    def test_submission_not_late(self, assignment, student_user):
        """Test submission before due date."""
        submission = AssignmentSubmission.objects.create(
            assignment=assignment,
            student=student_user,
            status='submitted',
            submitted_at=timezone.now()
        )
        
        assert submission.is_late() is False
    
    def test_submission_can_resubmit(self, submission_submitted):
        """Test can_resubmit() before grading."""
        assert submission_submitted.can_resubmit() is True
    
    def test_submission_cannot_resubmit_after_grading(self, submission_graded):
        """Test cannot resubmit after grading."""
        assert submission_graded.can_resubmit() is False
    
    def test_graded_submission(self, submission_graded):
        """Test graded submission."""
        assert submission_graded.status == 'graded'
        assert submission_graded.grade == 85
        assert submission_graded.feedback != ""
        assert submission_graded.graded_by is not None


# ============================================================================
# QUIZ MODEL TESTS
# ============================================================================

@pytest.mark.django_db
class TestQuizModel:
    """Test Quiz model."""
    
    def test_create_quiz(self, quiz):
        """Test creating a quiz."""
        assert quiz.title == "Variables Quiz"
        assert quiz.difficulty == 'medium'
        assert quiz.duration_minutes == 30
        assert quiz.passing_score == 70
        assert quiz.is_published is True
    
    def test_quiz_practice_mode(self, quiz_practice):
        """Test practice quiz."""
        assert quiz_practice.is_practice is True
        assert quiz_practice.duration_minutes == 0
    
    def test_quiz_question_count(self, complete_quiz):
        """Test question_count() method."""
        quiz = complete_quiz['quiz']
        assert quiz.question_count() == 4
    
    def test_quiz_total_points(self, complete_quiz):
        """Test total_points() calculation."""
        quiz = complete_quiz['quiz']
        total = quiz.total_points()
        assert total == 9  # 2 + 2 + 1 + 4
    
    def test_quiz_difficulty_choices(self, module, teacher_user):
        """Test valid difficulty levels."""
        difficulties = ['easy', 'medium', 'hard']
        
        for diff in difficulties:
            quiz = Quiz.objects.create(
                module=module,
                title=f"{diff.capitalize()} Quiz",
                difficulty=diff,
                duration_minutes=30,
                is_published=True,
                created_by=teacher_user
            )
            assert quiz.difficulty == diff


# ============================================================================
# QUIZ QUESTION TESTS
# ============================================================================

@pytest.mark.django_db
class TestQuizQuestionModel:
    """Test QuizQuestion model."""
    
    def test_create_mcq_question(self, question_mcq):
        """Test MCQ question creation."""
        assert question_mcq.question_type == 'mcq'
        assert len(question_mcq.options) == 4
        assert question_mcq.correct_answer in question_mcq.options
    
    def test_create_fill_question(self, question_fill):
        """Test fill-in-blank question."""
        assert question_fill.question_type == 'fill'
        assert question_fill.correct_answer == "container"
    
    def test_create_tf_question(self, question_tf):
        """Test true/false question."""
        assert question_tf.question_type == 'tf'
        assert question_tf.correct_answer.lower() in ['true', 'false']
    
    def test_create_match_question(self, question_match):
        """Test matching question."""
        assert question_match.question_type == 'match'
        assert len(question_match.matching_pairs) == 4
    
    def test_mcq_validation(self, quiz):
        """Test MCQ must have exactly 4 options."""
        with pytest.raises(ValidationError, match='exactly 4 options'):
            question = QuizQuestion(
                quiz=quiz,
                question_type='mcq',
                question_text="Test question",
                options=["Option 1", "Option 2"],
                correct_answer="Option 1",
                points=1
            )
            question.full_clean()
    
    def test_match_validation(self, quiz):
        """Test matching question must have exactly 4 pairs."""
        with pytest.raises(ValidationError, match='exactly 4 pairs'):
            question = QuizQuestion(
                quiz=quiz,
                question_type='match',
                question_text="Match these",
                matching_pairs=[
                    {"left": "A", "right": "1"},
                    {"left": "B", "right": "2"}
                ],
                correct_answer="See pairs",
                points=2
            )
            question.full_clean()


# ============================================================================
# QUIZ ATTEMPT TESTS
# ============================================================================

@pytest.mark.django_db
class TestQuizAttemptModel:
    """Test QuizAttempt model."""
    
    def test_create_quiz_attempt(self, quiz_attempt_in_progress):
        """Test creating a quiz attempt."""
        assert quiz_attempt_in_progress.status == 'in_progress'
        assert quiz_attempt_in_progress.attempt_number == 1
        assert quiz_attempt_in_progress.started_at is not None
    
    def test_submitted_quiz_attempt(self, quiz_attempt_submitted):
        """Test submitted quiz attempt."""
        assert quiz_attempt_submitted.status == 'submitted'
        assert quiz_attempt_submitted.score == 85
        assert quiz_attempt_submitted.passed is True
        assert quiz_attempt_submitted.time_taken_seconds == 1500
    
    def test_failed_quiz_attempt(self, quiz_attempt_failed):
        """Test failed quiz attempt."""
        assert quiz_attempt_failed.passed is False
        assert quiz_attempt_failed.score < quiz_attempt_failed.quiz.passing_score
    
    def test_calculate_score(self, quiz_attempt_in_progress):
        """Test calculate_score() method."""
        quiz_attempt_in_progress.total_points_earned = 7
        quiz_attempt_in_progress.total_points_possible = 10
        quiz_attempt_in_progress.calculate_score()
        
        assert quiz_attempt_in_progress.score == 70
        assert quiz_attempt_in_progress.passed is True


# ============================================================================
# QUIZ ATTEMPT ANSWER TESTS
# ============================================================================

@pytest.mark.django_db
class TestQuizAttemptAnswerModel:
    """Test QuizAttemptAnswer model."""
    
    def test_check_answer_mcq_correct(self, quiz_attempt_in_progress, question_mcq):
        """Test checking correct MCQ answer."""
        answer = QuizAttemptAnswer.objects.create(
            attempt=quiz_attempt_in_progress,
            question=question_mcq,
            answer="A container for storing data"
        )
        
        result = answer.check_answer()
        
        assert result is True
        assert answer.is_correct is True
        assert answer.points_earned == question_mcq.points
    
    def test_check_answer_mcq_incorrect(self, quiz_attempt_in_progress, question_mcq):
        """Test checking incorrect MCQ answer."""
        answer = QuizAttemptAnswer.objects.create(
            attempt=quiz_attempt_in_progress,
            question=question_mcq,
            answer="A fixed value"
        )
        
        result = answer.check_answer()
        
        assert result is False
        assert answer.is_correct is False
        assert answer.points_earned == 0
    
    def test_check_answer_fill_case_insensitive(self, quiz_attempt_in_progress, question_fill):
        """Test fill-in-blank is case-insensitive."""
        answer = QuizAttemptAnswer.objects.create(
            attempt=quiz_attempt_in_progress,
            question=question_fill,
            answer="CONTAINER"
        )
        
        result = answer.check_answer()
        
        assert result is True
        assert answer.is_correct is True
    
    def test_check_answer_tf(self, quiz_attempt_in_progress, question_tf):
        """Test true/false answer checking."""
        answer = QuizAttemptAnswer.objects.create(
            attempt=quiz_attempt_in_progress,
            question=question_tf,
            answer="true"
        )
        
        result = answer.check_answer()
        
        assert result is True
        assert answer.is_correct is True
    
    def test_check_answer_match_correct(self, quiz_attempt_in_progress, question_match):
        """Test matching answer checking."""
        answer = QuizAttemptAnswer.objects.create(
            attempt=quiz_attempt_in_progress,
            question=question_match,
            matching_answer=[
                {"left": "Integer", "right": "42"},
                {"left": "String", "right": "Hello"},
                {"left": "Boolean", "right": "True"},
                {"left": "Float", "right": "3.14"}
            ]
        )
        
        result = answer.check_answer()
        
        assert result is True
        assert answer.is_correct is True


# ============================================================================
# FLASHCARD MODEL TESTS
# ============================================================================

@pytest.mark.django_db
class TestFlashcardModel:
    """Test Flashcard model."""
    
    def test_create_flashcard(self, flashcard):
        """Test creating a flashcard."""
        assert flashcard.question == "What is a variable?"
        assert flashcard.answer != ""
        assert flashcard.hint != ""
        assert flashcard.is_active is True
    
    def test_flashcard_ai_generated(self, flashcard_ai):
        """Test AI-generated flashcard."""
        assert flashcard_ai.is_ai_generated is True
    
    def test_flashcard_inactive(self, flashcard_inactive):
        """Test inactive flashcard."""
        assert flashcard_inactive.is_active is False
    
    def test_flashcard_ordering(self, multiple_flashcards):
        """Test flashcards are ordered."""
        cards = list(Flashcard.objects.filter(module=multiple_flashcards[0].module))
        
        for i in range(len(cards) - 1):
            assert cards[i].order <= cards[i + 1].order


# ============================================================================
# FLASHCARD PROGRESS TESTS (SRS)
# ============================================================================

@pytest.mark.django_db
class TestFlashcardProgressModel:
    """Test FlashcardProgress model and SRS algorithm."""
    
    def test_create_flashcard_progress(self, flashcard_progress_new):
        """Test creating flashcard progress."""
        assert flashcard_progress_new.ease_factor == 2.5
        assert flashcard_progress_new.interval_days == 1
        assert flashcard_progress_new.repetitions == 0
        assert flashcard_progress_new.is_mastered is False
    
    def test_flashcard_progress_mastered(self, flashcard_progress_mastered):
        """Test mastered flashcard."""
        assert flashcard_progress_mastered.is_mastered is True
        assert flashcard_progress_mastered.ease_factor >= 2.5
        assert flashcard_progress_mastered.interval_days >= 21
    
    def test_is_due_for_review(self, flashcard_progress_due):
        """Test is_due_for_review() method."""
        assert flashcard_progress_due.is_due_for_review() is True
    
    def test_not_due_for_review(self, flashcard_progress_learning):
        """Test card not yet due."""
        assert flashcard_progress_learning.is_due_for_review() is False
    
    def test_update_srs_correct_answer(self, flashcard_progress_new):
        """Test SRS update with correct answer (quality 5)."""
        old_interval = flashcard_progress_new.interval_days
        old_repetitions = flashcard_progress_new.repetitions
        
        new_params = flashcard_progress_new.update_srs(quality=5)
        
        assert flashcard_progress_new.repetitions > old_repetitions
        assert flashcard_progress_new.ease_factor >= 2.5
        assert flashcard_progress_new.total_reviews == 1
        assert flashcard_progress_new.correct_reviews == 1
    
    def test_update_srs_incorrect_answer(self, flashcard_progress_learning):
        """Test SRS update with incorrect answer (quality 1)."""
        old_repetitions = flashcard_progress_learning.repetitions
        
        new_params = flashcard_progress_learning.update_srs(quality=1)
        
        assert flashcard_progress_learning.repetitions == 0
        assert flashcard_progress_learning.interval_days == 1
    
    def test_update_srs_quality_validation(self, flashcard_progress_new):
        """Test SRS quality must be 0-5."""
        with pytest.raises(ValidationError, match='between 0 and 5'):
            flashcard_progress_new.update_srs(quality=6)
    
    def test_reset_progress(self, flashcard_progress_learning):
        """Test reset_progress() method."""
        flashcard_progress_learning.reset_progress()
        
        assert flashcard_progress_learning.ease_factor == 2.5
        assert flashcard_progress_learning.interval_days == 1
        assert flashcard_progress_learning.repetitions == 0
        assert flashcard_progress_learning.total_reviews == 0
        assert flashcard_progress_learning.is_mastered is False
    
    def test_unique_flashcard_student(self, flashcard_progress_new):
        """Test flashcard + student must be unique."""
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                FlashcardProgress.objects.create(
                    flashcard=flashcard_progress_new.flashcard,
                    student=flashcard_progress_new.student,
                    ease_factor=2.5,
                    interval_days=1
                )


# ============================================================================
# WORKSHEET MODEL TESTS
# ============================================================================

@pytest.mark.django_db
class TestWorksheetModel:
    """Test Worksheet model."""
    
    def test_create_worksheet(self, worksheet):
        """Test creating a worksheet."""
        assert worksheet.title == "Variables Practice Worksheet"
        assert worksheet.topic == "Variables and Expressions"
        assert worksheet.difficulty == 'medium'
        assert worksheet.is_ai_generated is True
    
    def test_worksheet_with_answer_key(self, worksheet_with_answers):
        """Test worksheet with answer key."""
        assert worksheet_with_answers.worksheet_file is not None
        assert worksheet_with_answers.answer_key_file is not None
    
    def test_worksheet_str_representation(self, worksheet):
        """Test __str__ method."""
        assert worksheet.title in str(worksheet)