"""
Communications App Managers

Custom model managers for:
- ChatSession (active sessions, student sessions)
- ChatMessage (by role, recent messages)
- Notice (published, priority filtering)
"""

from django.db import models
from django.utils import timezone


class ChatSessionManager(models.Manager):
    """Custom manager for ChatSession model."""
    
    def active(self):
        """Get all active chat sessions."""
        return self.filter(status='active')
    
    def completed(self):
        """Get all completed sessions."""
        return self.filter(status='completed')
    
    def for_student(self, student):
        """
        Get all sessions for a specific student.
        
        Args:
            student: User instance
        
        Returns:
            QuerySet of ChatSession
        """
        return self.filter(student=student)
    
    def for_module(self, module):
        """
        Get all sessions for a specific module.
        
        Args:
            module: PathModule instance
        
        Returns:
            QuerySet of ChatSession
        """
        return self.filter(module=module)
    
    def recent(self, days=7):
        """
        Get sessions from last N days.
        
        Args:
            days: Number of days to look back
        
        Returns:
            QuerySet of recent ChatSession
        """
        cutoff = timezone.now() - timezone.timedelta(days=days)
        return self.filter(created_at__gte=cutoff)
    
    def with_analytics(self):
        """Get sessions with message count annotation."""
        return self.annotate(
            message_count=models.Count('messages')
        )


class ChatMessageManager(models.Manager):
    """Custom manager for ChatMessage model."""
    
    def student_messages(self):
        """Get all student messages."""
        return self.filter(role='student')
    
    def assistant_messages(self):
        """Get all AI assistant messages."""
        return self.filter(role='assistant')
    
    def for_session(self, session):
        """
        Get all messages for a session.
        
        Args:
            session: ChatSession instance
        
        Returns:
            QuerySet of ChatMessage ordered by timestamp
        """
        return self.filter(session=session).order_by('timestamp')
    
    def recent(self, limit=50):
        """
        Get most recent messages.
        
        Args:
            limit: Number of messages to return
        
        Returns:
            QuerySet of recent messages
        """
        return self.order_by('-timestamp')[:limit]
    
    def total_tokens_used(self):
        """Calculate total tokens used across all messages."""
        return self.aggregate(
            total=models.Sum('tokens_used')
        )['total'] or 0


class NoticeManager(models.Manager):
    """Custom manager for Notice model."""
    
    def published(self):
        """Get all published notices."""
        return self.filter(is_published=True)
    
    def unpublished(self):
        """Get all unpublished (draft) notices."""
        return self.filter(is_published=False)
    
    def for_offering(self, offering):
        """
        Get all notices for a course offering.
        
        Args:
            offering: CourseOffering instance
        
        Returns:
            QuerySet of Notice
        """
        return self.filter(course_offering=offering)
    
    def active(self):
        """
        Get active notices (published, not expired).
        
        Returns:
            QuerySet of active notices
        """
        now = timezone.now()
        return self.filter(
            is_published=True
        ).filter(
            models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=now)
        )
    
    def pinned(self):
        """Get pinned notices."""
        return self.filter(is_pinned=True, is_published=True)
    
    def by_priority(self, priority):
        """
        Filter by priority level.
        
        Args:
            priority: 'low', 'medium', 'high', 'urgent'
        
        Returns:
            QuerySet of Notice
        """
        return self.filter(priority=priority)
    
    def high_priority(self):
        """Get high and urgent priority notices."""
        return self.filter(priority__in=['high', 'urgent'])
    
    def visible_to_student(self, student):
        """
        Get notices visible to a specific student.
        
        Args:
            student: User instance (student role)
        
        Returns:
            QuerySet of visible notices
        """
        now = timezone.now()
        
        return self.filter(
            course_offering__enrollments__student=student,
            course_offering__enrollments__status='active',
            is_published=True
        ).filter(
            models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=now)
        ).filter(
            models.Q(visible_to_all=True) | 
            models.Q(visible_to_students=student)
        ).distinct()
    
    def recent(self, days=7):
        """
        Get notices created in last N days.
        
        Args:
            days: Number of days to look back
        
        Returns:
            QuerySet of recent notices
        """
        cutoff = timezone.now() - timezone.timedelta(days=days)
        return self.filter(created_at__gte=cutoff)