"""
Pytest fixtures for communications app tests.

Imports fixtures from root conftest and adds communication-specific fixtures.
"""

import pytest
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.communications.models import (
    ChatSession,
    ChatMessage,
    Notice,
)

User = get_user_model()

# NOTE: Root conftest.py provides these fixtures automatically:
# - academic_year, program, cohort, term_sem1, term_sem2
# - subject, course, class_section_university
# - course_offering, enrollment
# - student_user, student_user_2, teacher_user, dean_user, admin_user
# - university_setup, k12_setup


# ============================================================================
# COURSES APP FIXTURES (if not already in root)
# ============================================================================

@pytest.fixture
def course_path(course, teacher_user):
    """Create a CoursePath for testing."""
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
    """Create PathModule for testing."""
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
# CHAT SESSION FIXTURES
# ============================================================================

@pytest.fixture
def chat_session_active(student_user, module):
    """Create an active chat session."""
    return ChatSession.objects.create(
        student=student_user,
        module=module,
        title="How do variables work?",
        status='active',
        total_messages=0,
        total_time_seconds=0,
        context_snapshot={
            'module_title': module.title,
            'path_label': module.path.label,
            'created_at': timezone.now().isoformat()
        }
    )


@pytest.fixture
def chat_session_completed(student_user_2, module):
    """Create a completed chat session."""
    return ChatSession.objects.create(
        student=student_user_2,
        module=module,
        title="Understanding data types",
        status='completed',
        total_messages=10,
        total_time_seconds=1200,
        last_message_at=timezone.now() - timedelta(days=2),
        context_snapshot={
            'module_title': module.title,
            'created_at': (timezone.now() - timedelta(days=3)).isoformat()
        }
    )


@pytest.fixture
def chat_session_with_messages(student_user, module):
    """Create a chat session with multiple messages."""
    session = ChatSession.objects.create(
        student=student_user,
        module=module,
        title="Variables and Memory",
        status='active',
        total_messages=4,
        total_time_seconds=600,
        last_message_at=timezone.now()
    )
    
    # Create messages
    messages = [
        ChatMessage.objects.create(
            session=session,
            role='student',
            content='What is a variable?',
            tokens_used=0,
            timestamp=timezone.now() - timedelta(minutes=10)
        ),
        ChatMessage.objects.create(
            session=session,
            role='assistant',
            content='A variable is a named storage location that holds a value.',
            tokens_used=150,
            processing_time_ms=250,
            timestamp=timezone.now() - timedelta(minutes=9)
        ),
        ChatMessage.objects.create(
            session=session,
            role='student',
            content='Can you give me an example?',
            tokens_used=0,
            timestamp=timezone.now() - timedelta(minutes=5)
        ),
        ChatMessage.objects.create(
            session=session,
            role='assistant',
            content='Sure! In Python: `age = 25` stores the number 25 in a variable called age.',
            tokens_used=200,
            processing_time_ms=300,
            timestamp=timezone.now() - timedelta(minutes=4)
        ),
    ]
    
    return session


@pytest.fixture
def multiple_chat_sessions(student_user, module):
    """Create multiple chat sessions for testing."""
    sessions = []
    
    for i in range(5):
        session = ChatSession.objects.create(
            student=student_user,
            module=module,
            title=f"Chat Session {i + 1}",
            status='active' if i < 3 else 'completed',
            total_messages=i + 1,
            total_time_seconds=(i + 1) * 300,
            last_message_at=timezone.now() - timedelta(days=i)
        )
        sessions.append(session)
    
    return sessions


# ============================================================================
# CHAT MESSAGE FIXTURES
# ============================================================================

@pytest.fixture
def student_message(chat_session_active):
    """Create a student message."""
    return ChatMessage.objects.create(
        session=chat_session_active,
        role='student',
        content='How do I declare a variable in Python?',
        tokens_used=0
    )


@pytest.fixture
def assistant_message(chat_session_active):
    """Create an assistant message."""
    return ChatMessage.objects.create(
        session=chat_session_active,
        role='assistant',
        content='To declare a variable in Python, use: variable_name = value. For example: x = 10',
        tokens_used=180,
        processing_time_ms=320
    )


@pytest.fixture
def long_conversation(chat_session_active):
    """Create a long conversation (20 messages)."""
    messages = []
    
    for i in range(20):
        # Student message
        msg_student = ChatMessage.objects.create(
            session=chat_session_active,
            role='student',
            content=f'Student question {i + 1}',
            tokens_used=0,
            timestamp=timezone.now() - timedelta(minutes=40 - (i * 2))
        )
        messages.append(msg_student)
        
        # Assistant message
        msg_assistant = ChatMessage.objects.create(
            session=chat_session_active,
            role='assistant',
            content=f'AI answer {i + 1}',
            tokens_used=150 + (i * 10),
            processing_time_ms=200 + (i * 20),
            timestamp=timezone.now() - timedelta(minutes=39 - (i * 2))
        )
        messages.append(msg_assistant)
    
    # Update session metrics
    chat_session_active.total_messages = 40
    chat_session_active.last_message_at = messages[-1].timestamp
    chat_session_active.save()
    
    return messages


# ============================================================================
# NOTICE FIXTURES
# ============================================================================

@pytest.fixture
def notice_published(course_offering, teacher_user):
    """Create a published notice."""
    return Notice.objects.create(
        course_offering=course_offering,
        title="Important: Midterm Exam Schedule",
        content="<p>The midterm exam will be held next week on Wednesday.</p>",
        priority='high',
        is_published=True,
        visible_to_all=True,
        is_pinned=False,
        created_by=teacher_user,
        published_at=timezone.now()
    )


@pytest.fixture
def notice_draft(course_offering, teacher_user):
    """Create a draft notice."""
    return Notice.objects.create(
        course_offering=course_offering,
        title="Draft: Upcoming Assignment",
        content="<p>This is a draft notice about an assignment.</p>",
        priority='medium',
        is_published=False,
        visible_to_all=True,
        created_by=teacher_user
    )


@pytest.fixture
def notice_pinned(course_offering, teacher_user):
    """Create a pinned notice."""
    return Notice.objects.create(
        course_offering=course_offering,
        title="Pinned: Course Guidelines",
        content="<p>Please read the course guidelines carefully.</p>",
        priority='medium',
        is_published=True,
        visible_to_all=True,
        is_pinned=True,
        created_by=teacher_user,
        published_at=timezone.now()
    )


@pytest.fixture
def notice_urgent(course_offering, teacher_user):
    """Create an urgent notice."""
    return Notice.objects.create(
        course_offering=course_offering,
        title="URGENT: Class Cancelled Today",
        content="<p>Today's class is cancelled due to unforeseen circumstances.</p>",
        priority='urgent',
        is_published=True,
        visible_to_all=True,
        is_pinned=True,
        created_by=teacher_user,
        published_at=timezone.now()
    )


@pytest.fixture
def notice_expired(course_offering, teacher_user):
    """Create an expired notice."""
    return Notice.objects.create(
        course_offering=course_offering,
        title="Expired: Old Announcement",
        content="<p>This notice has expired.</p>",
        priority='low',
        is_published=True,
        visible_to_all=True,
        expires_at=timezone.now() - timedelta(days=1),
        created_by=teacher_user,
        published_at=timezone.now() - timedelta(days=7)
    )


@pytest.fixture
def notice_specific_students(course_offering, student_user, student_user_2, teacher_user):
    """Create a notice visible to specific students only."""
    notice = Notice.objects.create(
        course_offering=course_offering,
        title="Personal: Extra Help Session",
        content="<p>Special help session for selected students.</p>",
        priority='medium',
        is_published=True,
        visible_to_all=False,
        created_by=teacher_user,
        published_at=timezone.now()
    )
    
    # Add specific students
    notice.visible_to_students.add(student_user, student_user_2)
    
    return notice


@pytest.fixture
def multiple_notices(course_offering, teacher_user):
    """Create multiple notices for testing."""
    notices = []
    
    priorities = ['low', 'medium', 'high', 'urgent']
    
    for i in range(10):
        notice = Notice.objects.create(
            course_offering=course_offering,
            title=f"Notice {i + 1}",
            content=f"<p>Content for notice {i + 1}</p>",
            priority=priorities[i % 4],
            is_published=i < 7,  # First 7 are published
            visible_to_all=True,
            is_pinned=i < 2,  # First 2 are pinned
            created_by=teacher_user,
            published_at=timezone.now() if i < 7 else None,
            created_at=timezone.now() - timedelta(days=10 - i)
        )
        notices.append(notice)
    
    return notices


# ============================================================================
# COMBINED FIXTURES
# ============================================================================

@pytest.fixture
def communication_setup(
    student_user,
    teacher_user,
    module,
    course_offering,
    chat_session_active,
    notice_published
):
    """
    Complete communication setup with all components.
    
    Returns dict with all fixtures for convenience.
    """
    return {
        'student': student_user,
        'teacher': teacher_user,
        'module': module,
        'offering': course_offering,
        'session': chat_session_active,
        'notice': notice_published,
    }