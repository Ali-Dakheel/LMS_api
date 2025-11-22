from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class ChatSessionMetric(models.Model):
    """
    Aggregated chat session metrics per module.
    
    Features:
    - Total messages count
    - Total time spent
    - Session status tracking
    - Active/completed sessions count
    
    Aggregates ChatSession data for dashboards.
    """
    
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='chat_metrics',
        limit_choices_to={'role': 'student'},
        db_index=True
    )
    
    module = models.ForeignKey(
        'courses.PathModule',
        on_delete=models.CASCADE,
        related_name='chat_metrics',
        db_index=True
    )
    
    # Metrics
    total_sessions = models.PositiveIntegerField(
        default=0,
        help_text="Total number of chat sessions"
    )
    
    active_sessions = models.PositiveIntegerField(
        default=0,
        help_text="Number of active sessions"
    )
    
    completed_sessions = models.PositiveIntegerField(
        default=0,
        help_text="Number of completed sessions"
    )
    
    total_messages = models.PositiveIntegerField(
        default=0,
        help_text="Total messages across all sessions"
    )
    
    total_time_seconds = models.PositiveIntegerField(
        default=0,
        help_text="Total time spent chatting (seconds)"
    )
    
    # Last activity
    last_chat_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'chat_session_metrics'
        verbose_name_plural = 'Chat Session Metrics'
        unique_together = ['student', 'module']
        ordering = ['-last_chat_at']
        indexes = [
            models.Index(fields=['student']),
            models.Index(fields=['module']),
            models.Index(fields=['last_chat_at']),
        ]
    
    def __str__(self):
        return f"{self.student.name} - {self.module.title} ({self.total_messages} msgs)"
    
    def calculate_metrics(self):
        """
        Calculate metrics from ChatSession records.
        
        Returns:
            dict: Updated metrics
        """
        from apps.communications.models import ChatSession
        
        sessions = ChatSession.objects.filter(
            student=self.student,
            module=self.module
        )
        
        self.total_sessions = sessions.count()
        self.active_sessions = sessions.filter(status='active').count()
        self.completed_sessions = sessions.filter(status='completed').count()
        
        # Aggregate messages and time
        aggregates = sessions.aggregate(
            total_messages=models.Sum('total_messages'),
            total_time=models.Sum('total_time_seconds')
        )
        
        self.total_messages = aggregates['total_messages'] or 0
        self.total_time_seconds = aggregates['total_time'] or 0
        
        # Get last chat time
        last_session = sessions.order_by('-last_message_at').first()
        self.last_chat_at = last_session.last_message_at if last_session else None
        
        self.save()
        
        return {
            'total_sessions': self.total_sessions,
            'total_messages': self.total_messages,
            'total_time_seconds': self.total_time_seconds,
        }
