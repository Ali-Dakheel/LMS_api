import logging
from django.utils import timezone
from django.db.models import Avg
from decimal import Decimal

logger = logging.getLogger(__name__)
def get_student_dashboard_data(student):
    """
    Get comprehensive dashboard data for a student.
    
    Args:
        student: User instance
    
    Returns:
        dict: Dashboard data with all metrics
    """
    from apps.progress.models import (
        LessonProgress,
        LearningPathProgress,
        QuizAttemptSummary,
        AssignmentProgress,
        TopicAnalytics
    )
    from apps.academics.models import Enrollment
    
    # Get enrolled courses
    enrollments = Enrollment.objects.filter(
        student=student,
        status='active'
    ).select_related('offering__course')
    
    enrolled_courses = []
    for enrollment in enrollments:
        course = enrollment.offering.course
        
        # Calculate course progress
        paths = course.paths.filter(scope='course', is_published=True)
        path_progress_list = LearningPathProgress.objects.filter(
            student=student,
            path__in=paths
        )
        
        if path_progress_list.exists():
            avg_progress = path_progress_list.aggregate(
                avg=Avg('completion_percentage')
            )['avg'] or Decimal('0.00')
        else:
            avg_progress = Decimal('0.00')
        
        enrolled_courses.append({
            'course': course,
            'offering': enrollment.offering,
            'progress_percentage': avg_progress
        })
    
    # Get upcoming assignments (due within 7 days)
    upcoming_cutoff = timezone.now() + timezone.timedelta(days=7)
    upcoming_assignments = AssignmentProgress.objects.filter(
        student=student,
        status='not_submitted',
        assignment__due_date__lte=upcoming_cutoff,
        assignment__is_published=True
    ).order_by('assignment__due_date')[:5]
    
    # Get pending quizzes (not attempted yet)
    from apps.assessments.models import Quiz
    attempted_quizzes = QuizAttemptSummary.objects.filter(
        student=student
    ).values_list('quiz_id', flat=True)
    
    # Get weak topics across all courses
    weak_topics = TopicAnalytics.objects.filter(
        student=student
    ).weak_topics()[:5]
    
    # Calculate learning streak (days active in last 30 days)
    last_30_days = timezone.now() - timezone.timedelta(days=30)
    active_days = LessonProgress.objects.filter(
        student=student,
        last_accessed_at__gte=last_30_days
    ).dates('last_accessed_at', 'day').count()
    
    return {
        'enrolled_courses': enrolled_courses,
        'upcoming_assignments': upcoming_assignments,
        'weak_topics': weak_topics,
        'learning_streak_days': active_days,
    }