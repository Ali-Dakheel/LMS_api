"""
Progress Services
"""

from .progress import (
    update_lesson_progress,
    update_path_progress,
    update_quiz_summary,
    update_flashcard_set_progress,
    update_assignment_progress,
    update_chat_metrics,
)

from .requirements import (
    check_path_requirements,
    unlock_next_path,
)

from .analytics import (
    calculate_topic_analytics,
    get_weak_topics,
)

from .dashboard import get_student_dashboard_data

__all__ = [
    'update_lesson_progress',
    'update_path_progress',
    'update_quiz_summary',
    'update_flashcard_set_progress',
    'update_assignment_progress',
    'update_chat_metrics',
    'check_path_requirements',
    'unlock_next_path',
    'calculate_topic_analytics',
    'get_weak_topics',
    'get_student_dashboard_data',
]