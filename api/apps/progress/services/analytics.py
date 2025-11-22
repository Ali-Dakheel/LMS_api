from decimal import Decimal

def calculate_topic_analytics(student, course):
    """
    Calculate AI-analyzed topic strengths/weaknesses for a student in a course.
    
    This is a simplified version - full AI analysis would be in ai_tools app.
    
    Args:
        student: User instance
        course: Course instance
    
    Returns:
        list: List of TopicAnalytics instances
    """
    from apps.progress.models import (
        TopicAnalytics,
        QuizAttemptSummary,
        AssignmentProgress,
        FlashcardSetProgress
    )
    from apps.courses.models import PathModule
    
    # Get all modules for this course
    modules = PathModule.objects.filter(
        path__course=course,
        path__scope='course',
        is_published=True
    )
    
    # Group by category (topic)
    topics = modules.values_list('category', flat=True).distinct()
    
    analytics_list = []
    
    for topic in topics:
        topic_modules = modules.filter(category=topic)
        
        # Calculate averages
        quiz_scores = []
        assignment_grades = []
        flashcard_masteries = []
        
        for module in topic_modules:
            # Quiz scores
            quiz_summaries = QuizAttemptSummary.objects.filter(
                student=student,
                quiz__module=module
            )
            quiz_scores.extend([s.best_score for s in quiz_summaries])
            
            # Assignment grades
            assignment_progress = AssignmentProgress.objects.filter(
                student=student,
                assignment__module=module,
                grade__isnull=False
            )
            assignment_grades.extend([p.grade for p in assignment_progress])
            
            # Flashcard mastery
            flashcard_progress = FlashcardSetProgress.objects.filter(
                student=student,
                module=module
            ).first()
            if flashcard_progress:
                flashcard_masteries.append(float(flashcard_progress.mastery_percentage))
        
        # Calculate averages
        quiz_avg = Decimal(sum(quiz_scores) / len(quiz_scores)) if quiz_scores else None
        assignment_avg = Decimal(sum(assignment_grades) / len(assignment_grades)) if assignment_grades else None
        flashcard_avg = Decimal(sum(flashcard_masteries) / len(flashcard_masteries)) if flashcard_masteries else None
        
        # Calculate overall strength score (weighted average)
        scores = []
        if quiz_avg is not None:
            scores.append(float(quiz_avg) * 0.4)  # 40% weight
        if assignment_avg is not None:
            scores.append(float(assignment_avg) * 0.4)  # 40% weight
        if flashcard_avg is not None:
            scores.append(float(flashcard_avg) * 0.2)  # 20% weight
        
        if scores:
            strength_score = Decimal(sum(scores) / len(scores))
        else:
            strength_score = Decimal('0.00')
        
        # Create or update analytics
        analytics, created = TopicAnalytics.objects.update_or_create(
            student=student,
            course=course,
            topic_name=topic,
            defaults={
                'strength_score': strength_score,
                'quiz_average': quiz_avg,
                'assignment_average': assignment_avg,
                'flashcard_mastery': flashcard_avg,
            }
        )
        
        analytics.calculate_strength_level()
        analytics_list.append(analytics)
    
    return analytics_list


def get_weak_topics(student, course):
    """
    Get weak topics for a student in a course.
    
    Args:
        student: User instance
        course: Course instance
    
    Returns:
        QuerySet of TopicAnalytics (weak topics only)
    """
    from apps.progress.models import TopicAnalytics
    
    return TopicAnalytics.objects.filter(
        student=student,
        course=course
    ).weak_topics().order_by('strength_score')
