"""
Auto-Grading Service
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def grade_quiz_attempt(attempt) -> Dict[str, Any]:
    """
    Auto-grade a quiz attempt.
    
    Args:
        attempt: QuizAttempt instance
    
    Returns:
        dict: Grading results {
            'score': int,
            'total_questions': int,
            'correct_count': int,
            'passed': bool
        }
    """
    total_points = 0
    earned_points = 0
    correct_count = 0
    total_questions = 0
    
    # Grade each answer
    for answer in attempt.answers.all():
        total_questions += 1
        total_points += answer.question.points
        
        # Auto-check answer
        answer.check_answer()
        
        if answer.is_correct:
            correct_count += 1
            earned_points += answer.points_earned
    
    # Update attempt
    attempt.total_points_possible = total_points
    attempt.total_points_earned = earned_points
    attempt.calculate_score()
    
    logger.info(
        f"Quiz attempt {attempt.id} graded: {correct_count}/{total_questions} correct, "
        f"Score: {attempt.score}%"
    )
    
    return {
        'score': attempt.score,
        'total_questions': total_questions,
        'correct_count': correct_count,
        'passed': attempt.passed
    }