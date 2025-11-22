"""
Unit tests for Communications app models.

Tests:
- ChatSession creation and management
- ChatMessage creation and analytics
- Notice visibility and expiration
- Manager methods
- Business logic methods
"""

import pytest
from datetime import timedelta
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone

from apps.communications.models import (
    ChatSession,
    ChatMessage,
    Notice,
)


# ============================================================================
# CHAT SESSION MODEL TESTS
# ============================================================================

@pytest.mark.django_db
class TestChatSessionModel:
    """Test ChatSession model."""
    
    def test_create_chat_session(self, chat_session_active):
        """Test creating a chat session."""
        assert chat_session_active.title == "How do variables work?"
        assert chat_session_active.status == 'active'
        assert chat_session_active.total_messages == 0
        assert chat_session_active.is_active() is True
    
    def test_chat_session_str_representation(self, chat_session_active, student_user):
        """Test __str__ method."""
        assert student_user.name in str(chat_session_active)
        assert "How do variables work" in str(chat_session_active)
    
    def test_session_is_active(self, chat_session_active):
        """Test is_active() method."""
        assert chat_session_active.is_active() is True
        
        chat_session_active.status = 'completed'
        assert chat_session_active.is_active() is False
    
    def test_mark_session_completed(self, chat_session_active):
        """Test mark_completed() method."""
        chat_session_active.mark_completed()
        
        assert chat_session_active.status == 'completed'
    
    def test_add_message_to_session(self, chat_session_active):
        """Test add_message() method."""
        message = chat_session_active.add_message(
            role='student',
            content='What is a variable?',
            tokens_used=0
        )
        
        assert message.session == chat_session_active
        assert message.role == 'student'
        assert message.content == 'What is a variable?'
        assert chat_session_active.total_messages == 1
        assert chat_session_active.last_message_at is not None
    
    def test_add_multiple_messages(self, chat_session_active):
        """Test adding multiple messages updates metrics."""
        chat_session_active.add_message('student', 'Question 1')
        chat_session_active.add_message('assistant', 'Answer 1')
        chat_session_active.add_message('student', 'Question 2')
        
        chat_session_active.refresh_from_db()
        assert chat_session_active.total_messages == 3
        assert chat_session_active.messages.count() == 3
    
    def test_empty_session_duration(self, chat_session_active):
        """Test duration calculation for session with no messages."""
        duration = chat_session_active.calculate_duration()
        assert duration == 0
    
    def test_single_message_duration(self, chat_session_active):
        """Test duration with only one message."""
        chat_session_active.add_message('student', 'Single message')
        
        duration = chat_session_active.calculate_duration()
        # Single message has no duration (same timestamp for first and last)
        assert duration == 0
    
    def test_completed_session(self, chat_session_completed):
        """Test completed session properties."""
        assert chat_session_completed.status == 'completed'
        assert chat_session_completed.total_messages == 10
        assert chat_session_completed.total_time_seconds == 1200
        assert chat_session_completed.last_message_at is not None


# ============================================================================
# CHAT MESSAGE MODEL TESTS
# ============================================================================

@pytest.mark.django_db
class TestChatMessageModel:
    """Test ChatMessage model."""
    
    def test_create_student_message(self, student_message):
        """Test creating a student message."""
        assert student_message.role == 'student'
        assert student_message.content == 'How do I declare a variable in Python?'
        assert student_message.tokens_used == 0
        assert student_message.is_from_student() is True
        assert student_message.is_from_assistant() is False
    
    def test_create_assistant_message(self, assistant_message):
        """Test creating an assistant message."""
        assert assistant_message.role == 'assistant'
        assert assistant_message.tokens_used == 180
        assert assistant_message.processing_time_ms == 320
        assert assistant_message.is_from_student() is False
        assert assistant_message.is_from_assistant() is True
    
    def test_message_str_representation(self, student_message):
        """Test __str__ method."""
        str_repr = str(student_message)
        assert 'Student' in str_repr
        assert 'How do I declare' in str_repr
    
    def test_message_ordering(self, chat_session_with_messages):
        """Test messages are ordered by timestamp."""
        messages = list(chat_session_with_messages.messages.all())
        
        for i in range(len(messages) - 1):
            assert messages[i].timestamp <= messages[i + 1].timestamp
    
    def test_long_conversation(self, long_conversation):
        """Test session with many messages."""
        assert len(long_conversation) == 40
        
        # Count by role
        student_count = sum(1 for msg in long_conversation if msg.role == 'student')
        assistant_count = sum(1 for msg in long_conversation if msg.role == 'assistant')
        
        assert student_count == 20
        assert assistant_count == 20
    
    def test_token_tracking(self, long_conversation):
        """Test token usage tracking."""
        assistant_messages = [msg for msg in long_conversation if msg.role == 'assistant']
        
        total_tokens = sum(msg.tokens_used for msg in assistant_messages)
        assert total_tokens > 0


# ============================================================================
# CHAT SESSION MANAGER TESTS
# ============================================================================

@pytest.mark.django_db
class TestChatSessionManager:
    """Test ChatSession custom manager."""
    
    def test_active_sessions(self, multiple_chat_sessions):
        """Test active() manager method."""
        active = ChatSession.objects.active()
        
        assert active.count() == 3
        for session in active:
            assert session.status == 'active'
    
    def test_completed_sessions(self, multiple_chat_sessions):
        """Test completed() manager method."""
        completed = ChatSession.objects.completed()
        
        assert completed.count() == 2
        for session in completed:
            assert session.status == 'completed'
    
    def test_for_student(self, multiple_chat_sessions, student_user):
        """Test for_student() manager method."""
        sessions = ChatSession.objects.for_student(student_user)
        
        assert sessions.count() == 5
        for session in sessions:
            assert session.student == student_user
    
    def test_for_module(self, multiple_chat_sessions, module):
        """Test for_module() manager method."""
        sessions = ChatSession.objects.for_module(module)
        
        assert sessions.count() == 5
        for session in sessions:
            assert session.module == module
    
    def test_recent_sessions(self, multiple_chat_sessions):
        """Test recent() manager method."""
        recent = ChatSession.objects.recent(days=3)
        
        # Sessions created 0, 1, 2 days ago should be included
        assert recent.count() >= 3
    
    def test_with_analytics(self, chat_session_with_messages):
        """Test with_analytics() annotation."""
        sessions = ChatSession.objects.with_analytics()
        session = sessions.get(id=chat_session_with_messages.id)
        
        assert hasattr(session, 'message_count')
        assert session.message_count == 4


# ============================================================================
# CHAT MESSAGE MANAGER TESTS
# ============================================================================

@pytest.mark.django_db
class TestChatMessageManager:
    """Test ChatMessage custom manager."""
    
    def test_student_messages(self, long_conversation):
        """Test student_messages() manager method."""
        student_msgs = ChatMessage.objects.student_messages()
        
        assert student_msgs.count() == 20
        for msg in student_msgs:
            assert msg.role == 'student'
    
    def test_assistant_messages(self, long_conversation):
        """Test assistant_messages() manager method."""
        assistant_msgs = ChatMessage.objects.assistant_messages()
        
        assert assistant_msgs.count() == 20
        for msg in assistant_msgs:
            assert msg.role == 'assistant'
    
    def test_for_session(self, chat_session_with_messages):
        """Test for_session() manager method."""
        messages = ChatMessage.objects.for_session(chat_session_with_messages)
        
        assert messages.count() == 4
        # Check ordering
        timestamps = list(messages.values_list('timestamp', flat=True))
        assert timestamps == sorted(timestamps)
    
    def test_recent_messages(self, long_conversation):
        """Test recent() manager method."""
        recent = ChatMessage.objects.recent(limit=10)
        
        assert len(recent) == 10
    
    def test_total_tokens_used(self, long_conversation):
        """Test total_tokens_used() aggregation."""
        total = ChatMessage.objects.total_tokens_used()
        
        assert total > 0
        # Only assistant messages have tokens
        assert total == sum(msg.tokens_used for msg in long_conversation if msg.role == 'assistant')


# ============================================================================
# NOTICE MODEL TESTS
# ============================================================================

@pytest.mark.django_db
class TestNoticeModel:
    """Test Notice model."""
    
    def test_create_published_notice(self, notice_published):
        """Test creating a published notice."""
        assert notice_published.title == "Important: Midterm Exam Schedule"
        assert notice_published.priority == 'high'
        assert notice_published.is_published is True
        assert notice_published.visible_to_all is True
        assert notice_published.published_at is not None
    
    def test_create_draft_notice(self, notice_draft):
        """Test creating a draft notice."""
        assert notice_draft.is_published is False
        assert notice_draft.published_at is None
    
    def test_notice_str_representation(self, notice_published):
        """Test __str__ method."""
        str_repr = str(notice_published)
        assert "Important: Midterm Exam Schedule" in str_repr
    
    def test_pinned_notice(self, notice_pinned):
        """Test pinned notice."""
        assert notice_pinned.is_pinned is True
    
    def test_urgent_notice(self, notice_urgent):
        """Test urgent priority notice."""
        assert notice_urgent.priority == 'urgent'
        assert notice_urgent.is_pinned is True
    
    def test_notice_expiration(self, notice_expired):
        """Test is_expired() method."""
        assert notice_expired.is_expired() is True
    
    def test_active_notice_not_expired(self, notice_published):
        """Test active notice is not expired."""
        assert notice_published.is_expired() is False
    
    def test_notice_visible_to_all_students(self, notice_published, student_user):
        """Test is_visible_to() for public notice."""
        assert notice_published.is_visible_to(student_user) is True
    
    def test_notice_visible_to_specific_student(self, notice_specific_students, student_user, student_user_2):
        """Test visibility for specific students."""
        assert notice_specific_students.visible_to_all is False
        assert notice_specific_students.is_visible_to(student_user) is True
        assert notice_specific_students.is_visible_to(student_user_2) is True
    
    def test_expired_notice_not_visible(self, notice_expired, student_user):
        """Test expired notice is not visible."""
        assert notice_expired.is_visible_to(student_user) is False
    
    def test_draft_notice_not_visible(self, notice_draft, student_user):
        """Test draft notice is not visible."""
        assert notice_draft.is_visible_to(student_user) is False
    
    def test_publish_notice(self, notice_draft):
        """Test publish() method."""
        assert notice_draft.is_published is False
        
        notice_draft.publish()
        
        assert notice_draft.is_published is True
        assert notice_draft.published_at is not None
    
    def test_unpublish_notice(self, notice_published):
        """Test unpublish() method."""
        assert notice_published.is_published is True
        
        notice_published.unpublish()
        
        assert notice_published.is_published is False


# ============================================================================
# NOTICE MANAGER TESTS
# ============================================================================

@pytest.mark.django_db
class TestNoticeManager:
    """Test Notice custom manager."""
    
    def test_published_notices(self, multiple_notices):
        """Test published() manager method."""
        published = Notice.objects.published()
        
        assert published.count() == 7
        for notice in published:
            assert notice.is_published is True
    
    def test_unpublished_notices(self, multiple_notices):
        """Test unpublished() manager method."""
        unpublished = Notice.objects.unpublished()
        
        assert unpublished.count() == 3
        for notice in unpublished:
            assert notice.is_published is False
    
    def test_for_offering(self, multiple_notices, course_offering):
        """Test for_offering() manager method."""
        notices = Notice.objects.for_offering(course_offering)
        
        assert notices.count() == 10
    
    def test_active_notices(self, multiple_notices, notice_expired):
        """Test active() manager method (published and not expired)."""
        active = Notice.objects.active()
        
        # Should not include expired notice
        assert notice_expired not in active
        
        for notice in active:
            assert notice.is_published is True
            assert not notice.is_expired()
    
    def test_pinned_notices(self, multiple_notices):
        """Test pinned() manager method."""
        pinned = Notice.objects.pinned()
        
        assert pinned.count() == 2
        for notice in pinned:
            assert notice.is_pinned is True
            assert notice.is_published is True
    
    def test_by_priority(self, multiple_notices):
        """Test by_priority() manager method."""
        high_priority = Notice.objects.by_priority('high')
        
        for notice in high_priority:
            assert notice.priority == 'high'
    
    def test_high_priority_notices(self, multiple_notices, notice_urgent):
        """Test high_priority() manager method."""
        high = Notice.objects.high_priority()
        
        # Should include 'high' and 'urgent' priorities
        for notice in high:
            assert notice.priority in ['high', 'urgent']
    
    def test_visible_to_student(self, notice_published, notice_draft, student_user, enrollment):
        """Test visible_to_student() manager method."""
        visible = Notice.objects.visible_to_student(student_user)
        
        # Should include published notices in enrolled offerings
        assert notice_published in visible
        assert notice_draft not in visible
    
    def test_recent_notices(self, multiple_notices):
        """Test recent() manager method."""
        recent = Notice.objects.recent(days=7)
        
        # Most notices are recent (created within last 10 days)
        assert recent.count() >= 7