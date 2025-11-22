"""
Communications App Models - Smart Learning Hub

Database models for chat and notices:
- ChatSession (AI chatbot sessions per module)
- ChatMessage (individual messages with role)
- Notice (course-level announcements)
"""

from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth import get_user_model
from django.utils import timezone

from .managers import ChatSessionManager, ChatMessageManager, NoticeManager

User = get_user_model()


# ============================================================================
# CHAT SESSION MODEL
# ============================================================================

class ChatSession(models.Model):
    """
    Represents an AI chatbot session for a student within a module.
    
    Features:
    - Session-based (per module)
    - Context-aware (module content, book text, outcomes, student progress)
    - Message history tracking
    - Auto-titled sessions
    - Analytics (total messages, time spent)
    
    Sessions are created when student first asks a question in a module.
    """
    
    objects = ChatSessionManager()
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('archived', 'Archived'),
    ]
    
    # Student and module
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='chat_sessions',
        limit_choices_to={'role': 'student'},
        db_index=True,
        help_text="Student who owns this session"
    )
    
    module = models.ForeignKey(
        'courses.PathModule',
        on_delete=models.CASCADE,
        related_name='chat_sessions',
        db_index=True,
        help_text="Module this chat is about"
    )
    
    # Session metadata
    title = models.CharField(
        max_length=255,
        help_text="Auto-generated session title (from first message or AI)"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        db_index=True
    )
    
    # Analytics
    total_messages = models.PositiveIntegerField(
        default=0,
        help_text="Total messages in this session"
    )
    
    total_time_seconds = models.PositiveIntegerField(
        default=0,
        help_text="Total time spent in session (seconds)"
    )
    
    # Context tracking (for AI)
    context_snapshot = models.JSONField(
        null=True,
        blank=True,
        help_text="Snapshot of module content/progress when session started"
    )
    
    # Last activity
    last_message_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Timestamp of last message"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'chat_sessions'
        verbose_name_plural = 'Chat Sessions'
        ordering = ['-last_message_at', '-created_at']
        indexes = [
            models.Index(fields=['student', 'status']),
            models.Index(fields=['module', 'status']),
            models.Index(fields=['last_message_at']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.student.name} - {self.title[:50]}"
    
    def is_active(self):
        """Check if session is currently active."""
        return self.status == 'active'
    
    def mark_completed(self):
        """Mark session as completed."""
        self.status = 'completed'
        self.save(update_fields=['status'])
    
    def add_message(self, role, content, tokens_used=0):
        """
        Add a message to this session.
        
        Args:
            role: 'student' or 'assistant'
            content: Message text
            tokens_used: AI tokens used (for tracking)
        
        Returns:
            ChatMessage instance
        """
        message = self.messages.create(
            role=role,
            content=content,
            tokens_used=tokens_used
        )
        
        # Update session metrics
        self.total_messages += 1
        self.last_message_at = timezone.now()
        self.save(update_fields=['total_messages', 'last_message_at'])
        
        return message
    
    def calculate_duration(self):
        """Calculate session duration from first to last message."""
        if not self.messages.exists():
            return 0
        
        first_msg = self.messages.order_by('timestamp').first()
        last_msg = self.messages.order_by('timestamp').last()
        
        if first_msg and last_msg:
            duration = (last_msg.timestamp - first_msg.timestamp).total_seconds()
            return max(0, int(duration))
        
        return 0


# ============================================================================
# CHAT MESSAGE MODEL
# ============================================================================

class ChatMessage(models.Model):
    """
    Represents a single message in a chat session.
    
    Messages are exchanged between student and AI assistant.
    Tracks tokens for AI usage monitoring.
    """
    
    objects = ChatMessageManager()
    
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('assistant', 'AI Assistant'),
    ]
    
    session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name='messages',
        db_index=True
    )
    
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        db_index=True,
        help_text="Who sent this message"
    )
    
    content = models.TextField(
        help_text="Message content"
    )
    
    # AI tracking
    tokens_used = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Tokens used by AI (for cost tracking)"
    )
    
    # Processing metadata
    processing_time_ms = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="AI response time in milliseconds"
    )
    
    # Timestamps
    timestamp = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )
    
    class Meta:
        db_table = 'chat_messages'
        verbose_name_plural = 'Chat Messages'
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['session', 'timestamp']),
            models.Index(fields=['role']),
        ]
    
    def __str__(self):
        preview = self.content[:50]
        return f"{self.get_role_display()}: {preview}..."
    
    def is_from_student(self):
        """Check if message is from student."""
        return self.role == 'student'
    
    def is_from_assistant(self):
        """Check if message is from AI assistant."""
        return self.role == 'assistant'


# ============================================================================
# NOTICE MODEL
# ============================================================================

class Notice(models.Model):
    """
    Represents a course-level announcement/notice.
    
    Features:
    - CRUD operations
    - Rich text support
    - Priority levels
    - Visibility control (all students vs. specific students)
    - Timestamp tracking
    - Created by teacher
    
    Visible to students in the course offering.
    """
    
    objects = NoticeManager()
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    # Scope
    course_offering = models.ForeignKey(
        'academics.CourseOffering',
        on_delete=models.CASCADE,
        related_name='notices',
        db_index=True,
        help_text="Course offering this notice belongs to"
    )
    
    # Content
    title = models.CharField(
        max_length=255,
        help_text="Notice title"
    )
    
    content = models.TextField(
        help_text="Notice content (supports HTML/rich text)"
    )
    
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium',
        db_index=True,
        help_text="Notice priority level"
    )
    
    # Visibility
    is_published = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Published notices are visible to students"
    )
    
    visible_to_all = models.BooleanField(
        default=True,
        help_text="If False, only visible to specific students"
    )
    
    # Specific students (if not visible_to_all)
    visible_to_students = models.ManyToManyField(
        User,
        related_name='visible_notices',
        blank=True,
        limit_choices_to={'role': 'student'},
        help_text="Specific students who can see this notice"
    )
    
    # Pinned notice (stays at top)
    is_pinned = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Pinned notices appear at the top"
    )
    
    # Expiration
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Notice expires and hides after this date"
    )
    
    # Author
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_notices',
        limit_choices_to={'role__in': ['teacher', 'admin']},
        help_text="Teacher/admin who created this notice"
    )
    
    # Publishing
    published_at = models.DateTimeField(
        null=True,
        blank=True
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notices'
        verbose_name_plural = 'Notices'
        ordering = ['-is_pinned', '-created_at']
        indexes = [
            models.Index(fields=['course_offering', 'is_published']),
            models.Index(fields=['priority']),
            models.Index(fields=['is_pinned', '-created_at']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.course_offering})"
    
    def is_expired(self):
        """Check if notice has expired."""
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at
    
    def is_visible_to(self, student):
        """
        Check if notice is visible to specific student.
        
        Args:
            student: User instance (student role)
        
        Returns:
            bool: True if student can see this notice
        """
        if not self.is_published:
            return False
        
        if self.is_expired():
            return False
        
        if self.visible_to_all:
            return True
        
        return self.visible_to_students.filter(id=student.id).exists()
    
    def publish(self):
        """Publish this notice."""
        self.is_published = True
        self.published_at = timezone.now()
        self.save(update_fields=['is_published', 'published_at'])
    
    def unpublish(self):
        """Unpublish this notice."""
        self.is_published = False
        self.save(update_fields=['is_published'])