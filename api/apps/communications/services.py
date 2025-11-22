"""
Communications App Services

Business logic for:
- Chat context building (AI-aware)
- Notice visibility checking
- Session management
"""

import logging
from django.utils import timezone
from django.db.models import Q

logger = logging.getLogger(__name__)


# ============================================================================
# CHAT CONTEXT BUILDER
# ============================================================================

def build_chat_context(session):
    """
    Build context for AI chatbot based on session.
    
    Context includes:
    - Module content (title, description, outcomes)
    - Module details (lesson text)
    - Book pages (if module has book reference)
    - Student progress (completion %, quiz scores)
    - Previous chat messages
    
    Args:
        session: ChatSession instance
    
    Returns:
        dict: Contextual information for AI
    """
    module = session.module
    student = session.student
    
    context = {
        'module': {
            'title': module.title,
            'description': module.description,
            'category': module.category,
            'outcomes': module.outcomes,
        },
        'path': {
            'label': module.path.label,
            'objectives': module.path.objectives,
            'outcomes': module.path.outcomes,
        },
        'course': {
            'title': module.path.course.title,
            'subject': module.path.course.subject.name,
        },
        'student': {
            'name': student.name,
            'role': student.role,
        },
    }
    
    # Add module details if exists
    if hasattr(module, 'detail'):
        context['module']['content'] = module.detail.text_content[:2000]  # Limit for AI
        context['module']['objectives'] = module.detail.objectives
    
    # Add book context if module is from book
    if module.path.source_kind == 'book' and module.path.source_book:
        book = module.path.source_book
        context['book'] = {
            'title': book.title,
            'author': book.author,
        }
        
        # Add TOC item if exists
        if module.path.source_toc_item:
            toc_item = module.path.source_toc_item
            context['book']['chapter'] = {
                'title': toc_item.title,
                'level': toc_item.level,
            }
            
            # Add page text if available (sample)
            if toc_item.start_page:
                pages = book.pages.filter(
                    page_number__gte=toc_item.start_page,
                    page_number__lte=toc_item.start_page + 2  # First 3 pages
                ).values_list('text_content', flat=True)
                
                if pages:
                    context['book']['sample_text'] = '\n'.join(pages)[:1500]
    
    # Add student progress (stub for now - will complete when progress app is done)
    context['progress'] = {
        'placeholder': 'Progress tracking to be implemented'
    }
    
    # Add recent chat history (last 10 messages for context)
    messages = session.messages.order_by('-timestamp')[:10]
    context['chat_history'] = [
        {
            'role': msg.role,
            'content': msg.content,
            'timestamp': msg.timestamp.isoformat()
        }
        for msg in reversed(messages)
    ]
    
    return context


def generate_session_title(first_message):
    """
    Generate a session title from the first student message.
    
    Uses first 50 chars or AI-generated summary (stub for now).
    
    Args:
        first_message: str - First message from student
    
    Returns:
        str: Session title
    """
    # Simple implementation: use first 50 chars
    # TODO: Enhance with AI summarization when ai_tools is ready
    title = first_message[:50].strip()
    
    if len(first_message) > 50:
        title += "..."
    
    return title


# ============================================================================
# NOTICE VISIBILITY
# ============================================================================

def get_visible_notices_for_student(student, offering=None):
    """
    Get all notices visible to a student.
    
    Args:
        student: User instance (student role)
        offering: Optional CourseOffering to filter by
    
    Returns:
        QuerySet of Notice
    """
    from apps.communications.models import Notice
    
    notices = Notice.objects.visible_to_student(student)
    
    if offering:
        notices = notices.filter(course_offering=offering)
    
    return notices.order_by('-is_pinned', '-created_at')


def check_notice_visibility(notice, student):
    """
    Check if a notice is visible to a specific student.
    
    Args:
        notice: Notice instance
        student: User instance
    
    Returns:
        bool: True if visible
    """
    return notice.is_visible_to(student)


# ============================================================================
# SESSION MANAGEMENT
# ============================================================================

def get_or_create_session(student, module):
    """
    Get active session for student in module, or create new one.
    
    Args:
        student: User instance
        module: PathModule instance
    
    Returns:
        tuple: (ChatSession, created)
    """
    from apps.communications.models import ChatSession
    
    # Try to get active session
    session = ChatSession.objects.filter(
        student=student,
        module=module,
        status='active'
    ).first()
    
    if session:
        return session, False
    
    # Create new session
    session = ChatSession.objects.create(
        student=student,
        module=module,
        title="New Chat Session",  # Will be updated on first message
        status='active',
        context_snapshot=build_chat_context_snapshot(module, student)
    )
    
    logger.info(f"Created new chat session {session.id} for {student.email} in {module.title}")
    
    return session, True


def build_chat_context_snapshot(module, student):
    """
    Build a snapshot of context when session is created.
    
    Args:
        module: PathModule instance
        student: User instance
    
    Returns:
        dict: Context snapshot
    """
    return {
        'module_title': module.title,
        'module_category': module.category,
        'path_label': module.path.label,
        'course_title': module.path.course.title,
        'created_at': timezone.now().isoformat(),
    }


def close_inactive_sessions(days=7):
    """
    Close sessions that have been inactive for N days.
    
    Args:
        days: Number of days of inactivity
    
    Returns:
        int: Number of sessions closed
    """
    from apps.communications.models import ChatSession
    
    cutoff = timezone.now() - timezone.timedelta(days=days)
    
    inactive_sessions = ChatSession.objects.filter(
        status='active',
        last_message_at__lt=cutoff
    )
    
    count = inactive_sessions.count()
    inactive_sessions.update(status='completed')
    
    logger.info(f"Closed {count} inactive chat sessions")
    
    return count