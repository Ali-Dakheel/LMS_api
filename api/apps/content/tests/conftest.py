"""
Pytest fixtures for content app tests.
"""

import pytest
from datetime import datetime, timedelta
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.content.models import (
    Book,
    BookPage,
    BookTOCItem,
    BookAnalysisJob,
    ContentAccess,
)

User = get_user_model()


# ============================================================================
# BOOK FIXTURES
# ============================================================================

@pytest.fixture
def dummy_pdf_file():
    """Create a dummy PDF file for testing."""
    # Create minimal valid PDF content
    pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/Resources <<
/Font <<
/F1 <<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
>>
>>
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Hello World) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000317 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
410
%%EOF"""
    
    return SimpleUploadedFile(
        name='test_book.pdf',
        content=pdf_content,
        content_type='application/pdf'
    )


@pytest.fixture
def book(db, teacher_user, dummy_pdf_file):
    """Create a book with pending status."""
    return Book.objects.create(
        title="Introduction to Mathematics",
        author="John Doe",
        isbn="978-0-123456-78-9",
        publication_year=2024,
        description="A comprehensive guide to mathematics",
        pdf_file=dummy_pdf_file,
        file_size=1024 * 100,  # 100 KB
        status='pending',
        is_published=False,
        uploaded_by=teacher_user
    )


@pytest.fixture
def book_completed(db, teacher_user, dummy_pdf_file):
    """Create a book with completed processing status."""
    return Book.objects.create(
        title="Advanced Physics",
        author="Jane Smith",
        isbn="978-0-987654-32-1",
        publication_year=2023,
        pdf_file=dummy_pdf_file,
        file_size=1024 * 200,
        status='completed',
        total_pages=250,
        is_published=True,
        uploaded_by=teacher_user,
        processing_started_at=timezone.now() - timedelta(hours=2),
        processing_completed_at=timezone.now() - timedelta(hours=1)
    )


@pytest.fixture
def book_with_error(db, teacher_user, dummy_pdf_file):
    """Create a book with error status."""
    return Book.objects.create(
        title="Broken Book",
        author="Test Author",
        pdf_file=dummy_pdf_file,
        file_size=1024,
        status='error',
        error_message="Failed to extract text from PDF",
        uploaded_by=teacher_user
    )


@pytest.fixture
def published_book(db, teacher_user, dummy_pdf_file, course):
    """Create a published book linked to a course."""
    book = Book.objects.create(
        title="English Grammar Fundamentals",
        author="Grammar Expert",
        isbn="978-1-111111-11-1",
        pdf_file=dummy_pdf_file,
        file_size=1024 * 150,
        status='completed',
        total_pages=180,
        is_published=True,
        uploaded_by=teacher_user
    )
    book.courses.add(course)
    return book


@pytest.fixture
def multiple_books(db, teacher_user, dummy_pdf_file):
    """Create multiple books for testing."""
    books = []
    
    for i in range(1, 4):
        book = Book.objects.create(
            title=f"Test Book {i}",
            author=f"Author {i}",
            pdf_file=dummy_pdf_file,
            file_size=1024 * (50 * i),
            status='completed' if i % 2 == 0 else 'pending',
            is_published=i % 2 == 0,
            uploaded_by=teacher_user
        )
        books.append(book)
    
    return books


# ============================================================================
# BOOK PAGE FIXTURES
# ============================================================================

@pytest.fixture
def dummy_page_image():
    """Create a dummy page image."""
    # 1x1 PNG (smallest valid PNG)
    png_content = (
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
        b'\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00'
        b'\x00\x0cIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4'
        b'\x00\x00\x00\x00IEND\xaeB`\x82'
    )
    
    return SimpleUploadedFile(
        name='page_1.png',
        content=png_content,
        content_type='image/png'
    )


@pytest.fixture
def book_page(book_completed, dummy_page_image):
    """Create a book page."""
    return BookPage.objects.create(
        book=book_completed,
        page_number=1,
        page_image=dummy_page_image,
        extracted_text="This is the first page of the book with some sample text.",
        ocr_status='completed',
        ocr_confidence=0.95,
        ocr_completed_at=timezone.now()
    )


@pytest.fixture
def book_page_no_text(book_completed, dummy_page_image):
    """Create a book page without extracted text (needs OCR)."""
    return BookPage.objects.create(
        book=book_completed,
        page_number=2,
        page_image=dummy_page_image,
        extracted_text="",
        ocr_status='pending'
    )


@pytest.fixture
def multiple_pages(book_completed, dummy_page_image):
    """Create multiple pages for a book."""
    pages = []
    
    for i in range(1, 6):
        page = BookPage.objects.create(
            book=book_completed,
            page_number=i,
            page_image=dummy_page_image,
            extracted_text=f"Page {i} content with sample text.",
            ocr_status='completed',
            ocr_confidence=0.90 + (i * 0.01)
        )
        pages.append(page)
    
    return pages


# ============================================================================
# BOOK TOC FIXTURES
# ============================================================================

@pytest.fixture
def toc_chapter(book_completed):
    """Create a chapter-level TOC item."""
    return BookTOCItem.objects.create(
        book=book_completed,
        parent=None,
        level=1,
        title="Chapter 1: Introduction",
        start_page=1,
        end_page=25,
        slug="chapter-1-introduction",
        order=0,
        summary="Introduction to the main concepts",
        keywords="introduction, basics, fundamentals"
    )


@pytest.fixture
def toc_section(book_completed, toc_chapter):
    """Create a section-level TOC item."""
    return BookTOCItem.objects.create(
        book=book_completed,
        parent=toc_chapter,
        level=2,
        title="1.1 Overview",
        start_page=1,
        end_page=10,
        slug="1-1-overview",
        order=0,
        summary="Overview of the chapter",
        keywords="overview, summary"
    )


@pytest.fixture
def toc_subsection(book_completed, toc_section):
    """Create a subsection-level TOC item."""
    return BookTOCItem.objects.create(
        book=book_completed,
        parent=toc_section,
        level=3,
        title="1.1.1 Definitions",
        start_page=1,
        end_page=5,
        slug="1-1-1-definitions",
        order=0,
        summary="Key definitions",
        keywords="definitions, terms"
    )


@pytest.fixture
def complete_toc(book_completed):
    """Create a complete TOC hierarchy."""
    # Chapter 1
    chapter1 = BookTOCItem.objects.create(
        book=book_completed,
        level=1,
        title="Chapter 1: Introduction",
        start_page=1,
        end_page=50,
        slug="chapter-1",
        order=0
    )
    
    # Section 1.1
    section11 = BookTOCItem.objects.create(
        book=book_completed,
        parent=chapter1,
        level=2,
        title="1.1 Getting Started",
        start_page=1,
        end_page=25,
        slug="section-1-1",
        order=0
    )
    
    # Section 1.2
    section12 = BookTOCItem.objects.create(
        book=book_completed,
        parent=chapter1,
        level=2,
        title="1.2 Basic Concepts",
        start_page=26,
        end_page=50,
        slug="section-1-2",
        order=1
    )
    
    # Chapter 2
    chapter2 = BookTOCItem.objects.create(
        book=book_completed,
        level=1,
        title="Chapter 2: Advanced Topics",
        start_page=51,
        end_page=100,
        slug="chapter-2",
        order=1
    )
    
    return {
        'chapter1': chapter1,
        'section11': section11,
        'section12': section12,
        'chapter2': chapter2
    }


# ============================================================================
# BOOK ANALYSIS JOB FIXTURES
# ============================================================================

@pytest.fixture
def analysis_job_queued(book):
    """Create a queued analysis job."""
    return BookAnalysisJob.objects.create(
        book=book,
        job_type='full_processing',
        status='queued',
        total_items=1,
        max_retries=3
    )


@pytest.fixture
def analysis_job_processing(book):
    """Create a processing job."""
    return BookAnalysisJob.objects.create(
        book=book,
        job_type='text_extraction',
        status='processing',
        progress_percent=50,
        total_items=100,
        processed_items=50,
        started_at=timezone.now() - timedelta(minutes=10),
        celery_task_id='abc-123-def-456'
    )


@pytest.fixture
def analysis_job_completed(book_completed):
    """Create a completed job."""
    return BookAnalysisJob.objects.create(
        book=book_completed,
        job_type='full_processing',
        status='completed',
        progress_percent=100,
        total_items=1,
        processed_items=1,
        started_at=timezone.now() - timedelta(hours=1),
        completed_at=timezone.now() - timedelta(minutes=30)
    )


@pytest.fixture
def analysis_job_failed(book_with_error):
    """Create a failed job."""
    return BookAnalysisJob.objects.create(
        book=book_with_error,
        job_type='ocr',
        status='failed',
        error_message="OCR library not available",
        retry_count=3,
        max_retries=3,
        started_at=timezone.now() - timedelta(hours=2),
        completed_at=timezone.now() - timedelta(hours=2)
    )


# ============================================================================
# CONTENT ACCESS FIXTURES
# ============================================================================

@pytest.fixture
def content_access_course(student_user, course, admin_user):
    """Create content access for a course."""
    return ContentAccess.objects.create(
        user=student_user,
        content_type='course',
        content_id=course.id,
        permission='view',
        granted_by=admin_user,
        reason="Guest observer access"
    )


@pytest.fixture
def content_access_book(student_user, published_book, admin_user):
    """Create content access for a book."""
    return ContentAccess.objects.create(
        user=student_user,
        content_type='book',
        content_id=published_book.id,
        permission='view',
        expires_at=timezone.now() + timedelta(days=30),
        granted_by=admin_user,
        reason="30-day trial access"
    )


@pytest.fixture
def content_access_expired(student_user, course, admin_user):
    """Create expired content access."""
    return ContentAccess.objects.create(
        user=student_user,
        content_type='course',
        content_id=course.id,
        permission='view',
        expires_at=timezone.now() - timedelta(days=1),  # Expired yesterday
        granted_by=admin_user
    )