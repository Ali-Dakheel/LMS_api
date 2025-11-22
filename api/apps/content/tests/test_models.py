"""
Unit tests for Content app models.

Tests:
- Book creation and status tracking
- BookPage text extraction
- BookTOCItem hierarchy
- BookAnalysisJob processing
- ContentAccess permissions
"""

import pytest
from datetime import datetime, timedelta
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.content.models import (
    Book,
    BookPage,
    BookTOCItem,
    BookAnalysisJob,
    ContentAccess,
)


# ============================================================================
# BOOK MODEL TESTS
# ============================================================================

@pytest.mark.unit
@pytest.mark.database
class TestBookModel:
    """Test Book model."""
    
    def test_create_book(self, book):
        """Test creating a book."""
        assert book.title == "Introduction to Mathematics"
        assert book.author == "John Doe"
        assert book.isbn == "978-0-123456-78-9"
        assert book.status == 'pending'
        assert book.is_published is False
    
    def test_book_unique_isbn(self, book, dummy_pdf_file):
        """Test ISBN must be unique."""
        with pytest.raises(IntegrityError):
            Book.objects.create(
                title="Duplicate ISBN Book",
                isbn="978-0-123456-78-9",  # Duplicate
                pdf_file=dummy_pdf_file,
                file_size=1024
            )
    
    def test_book_file_size_auto_set(self, book):
        """Test file_size is automatically set from uploaded file."""
        assert book.file_size > 0
    
    def test_book_status_choices(self, book):
        """Test valid book status transitions."""
        statuses = ['pending', 'processing', 'completed', 'error']
        
        for status in statuses:
            book.status = status
            book.save()
            book.refresh_from_db()
            assert book.status == status
    
    def test_book_str_representation(self, book):
        """Test __str__ method."""
        assert str(book) == "Introduction to Mathematics by John Doe"
    
    def test_book_processing_timestamps(self, book_completed):
        """Test processing timestamp tracking."""
        assert book_completed.processing_started_at is not None
        assert book_completed.processing_completed_at is not None
        assert book_completed.processing_completed_at > book_completed.processing_started_at
    
    def test_book_keywords_storage(self, book):
        """Test keyword storage."""
        book.keywords = "mathematics, algebra, geometry, calculus"
        book.save()
        
        assert "algebra" in book.keywords
        assert "geometry" in book.keywords
    
    def test_book_courses_relationship(self, published_book, course):
        """Test many-to-many relationship with courses."""
        assert course in published_book.courses.all()
        assert published_book in course.textbooks.all()


# ============================================================================
# BOOK MANAGER TESTS
# ============================================================================

@pytest.mark.unit
class TestBookManager:
    """Test Book custom manager methods."""
    
    def test_published_only(self, published_book, book):
        """Test published_only() filters."""
        books = Book.objects.published_only()
        
        assert published_book in books
        assert book not in books  # Not published
    
    def test_completed_only(self, book_completed, book):
        """Test completed_only() filters."""
        books = Book.objects.completed_only()
        
        assert book_completed in books
        assert book not in books  # Pending
    
    def test_by_status(self, book, book_completed, book_with_error):
        """Test filtering by status."""
        pending_books = Book.objects.by_status('pending')
        assert book in pending_books
        
        completed_books = Book.objects.by_status('completed')
        assert book_completed in completed_books
        
        error_books = Book.objects.by_status('error')
        assert book_with_error in error_books
    
    def test_for_course(self, published_book, course):
        """Test for_course() filtering."""
        books = Book.objects.for_course(course)
        
        assert published_book in books


# ============================================================================
# BOOK PAGE TESTS
# ============================================================================

@pytest.mark.unit
class TestBookPageModel:
    """Test BookPage model."""
    
    def test_create_book_page(self, book_page):
        """Test creating a book page."""
        assert book_page.page_number == 1
        assert book_page.extracted_text != ""
        assert book_page.ocr_status == 'completed'
        assert book_page.ocr_confidence == 0.95
    
    def test_unique_book_page_number(self, book_page, dummy_page_image):
        """Test book + page_number must be unique."""
        with pytest.raises(IntegrityError):
            BookPage.objects.create(
                book=book_page.book,
                page_number=1,  # Duplicate
                page_image=dummy_page_image
            )
    
    def test_book_page_ocr_status(self, book_page_no_text):
        """Test page without text has pending OCR status."""
        assert book_page_no_text.extracted_text == ""
        assert book_page_no_text.ocr_status == 'pending'
    
    def test_book_page_str_representation(self, book_page):
        """Test __str__ method."""
        assert "Page 1" in str(book_page)
        assert book_page.book.title in str(book_page)
    
    def test_book_page_ordering(self, multiple_pages):
        """Test pages are ordered by page_number."""
        pages = list(BookPage.objects.filter(book=multiple_pages[0].book))
        
        for i in range(len(pages) - 1):
            assert pages[i].page_number < pages[i + 1].page_number


# ============================================================================
# BOOK TOC TESTS
# ============================================================================

@pytest.mark.unit
class TestBookTOCItemModel:
    """Test BookTOCItem model."""
    
    def test_create_toc_chapter(self, toc_chapter):
        """Test creating a chapter-level TOC item."""
        assert toc_chapter.level == 1
        assert toc_chapter.title == "Chapter 1: Introduction"
        assert toc_chapter.parent is None
        assert toc_chapter.start_page == 1
        assert toc_chapter.end_page == 25
    
    def test_create_toc_section(self, toc_section, toc_chapter):
        """Test creating a section under a chapter."""
        assert toc_section.level == 2
        assert toc_section.parent == toc_chapter
        assert toc_section.title == "1.1 Overview"
    
    def test_create_toc_subsection(self, toc_subsection, toc_section):
        """Test creating a subsection under a section."""
        assert toc_subsection.level == 3
        assert toc_subsection.parent == toc_section
    
    def test_toc_hierarchical_structure(self, complete_toc):
        """Test complete TOC hierarchy."""
        chapter1 = complete_toc['chapter1']
        
        # Chapter 1 has 2 children (sections)
        assert chapter1.children.count() == 2
        
        # Get children
        sections = list(chapter1.children.all())
        assert sections[0].title == "1.1 Getting Started"
        assert sections[1].title == "1.2 Basic Concepts"
    
    def test_toc_slug_auto_generated(self, book_completed):
        """Test slug is auto-generated from title."""
        toc_item = BookTOCItem.objects.create(
            book=book_completed,
            level=1,
            title="Chapter 2: Advanced Topics",
            start_page=51,
            end_page=100,
            order=1
        )
        
        assert toc_item.slug == "chapter-2-advanced-topics"
    
    def test_toc_unique_book_slug(self, toc_chapter):
        """Test book + slug must be unique."""
        with pytest.raises(IntegrityError):
            BookTOCItem.objects.create(
                book=toc_chapter.book,
                level=1,
                title="Different Title",
                slug="chapter-1-introduction",  # Duplicate slug
                start_page=100,
                end_page=150
            )
    
    def test_toc_str_representation(self, toc_chapter, toc_section):
        """Test __str__ method shows indentation."""
        # Chapter (level 1) has no indent
        chapter_str = str(toc_chapter)
        assert chapter_str.startswith("Chapter 1")
        
        # Section (level 2) has indent
        section_str = str(toc_section)
        assert section_str.startswith("  1.1")  # 2 spaces indent
    
    def test_toc_page_ranges(self, complete_toc):
        """Test page ranges are logical."""
        chapter1 = complete_toc['chapter1']
        section11 = complete_toc['section11']
        section12 = complete_toc['section12']
        
        # Chapter spans sections
        assert chapter1.start_page <= section11.start_page
        assert section11.end_page <= section12.start_page
        assert section12.end_page <= chapter1.end_page


# ============================================================================
# BOOK ANALYSIS JOB TESTS
# ============================================================================

@pytest.mark.unit
class TestBookAnalysisJobModel:
    """Test BookAnalysisJob model."""
    
    def test_create_analysis_job(self, analysis_job_queued):
        """Test creating an analysis job."""
        assert analysis_job_queued.job_type == 'full_processing'
        assert analysis_job_queued.status == 'queued'
        assert analysis_job_queued.progress_percent == 0
        assert analysis_job_queued.retry_count == 0
    
    def test_job_progress_tracking(self, analysis_job_processing):
        """Test progress tracking."""
        assert analysis_job_processing.status == 'processing'
        assert analysis_job_processing.progress_percent == 50
        assert analysis_job_processing.total_items == 100
        assert analysis_job_processing.processed_items == 50
    
    def test_job_completion(self, analysis_job_completed):
        """Test completed job."""
        assert analysis_job_completed.status == 'completed'
        assert analysis_job_completed.progress_percent == 100
        assert analysis_job_completed.completed_at is not None
    
    def test_job_failure_tracking(self, analysis_job_failed):
        """Test failed job tracking."""
        assert analysis_job_failed.status == 'failed'
        assert analysis_job_failed.error_message != ""
        assert analysis_job_failed.retry_count == 3
        assert analysis_job_failed.retry_count >= analysis_job_failed.max_retries
    
    def test_job_celery_task_id(self, analysis_job_processing):
        """Test Celery task ID storage."""
        assert analysis_job_processing.celery_task_id == 'abc-123-def-456'
    
    def test_job_str_representation(self, analysis_job_queued):
        """Test __str__ method."""
        job_str = str(analysis_job_queued)
        assert "Full Book Processing" in job_str
        assert "Queued" in job_str


# ============================================================================
# BOOK ANALYSIS JOB MANAGER TESTS
# ============================================================================

@pytest.mark.unit
class TestBookAnalysisJobManager:
    """Test BookAnalysisJob custom manager."""
    
    def test_pending_jobs(self, analysis_job_queued, analysis_job_processing, analysis_job_completed):
        """Test pending() returns queued and processing jobs."""
        pending = BookAnalysisJob.objects.pending()
        
        assert analysis_job_queued in pending
        assert analysis_job_processing in pending
        assert analysis_job_completed not in pending
    
    def test_failed_jobs(self, analysis_job_failed, analysis_job_completed):
        """Test failed() returns only failed jobs."""
        failed = BookAnalysisJob.objects.failed()
        
        assert analysis_job_failed in failed
        assert analysis_job_completed not in failed
    
    def test_retryable_jobs(self, analysis_job_failed):
        """Test retryable() finds jobs that can be retried."""
        # Create a retryable job (retry_count < max_retries)
        retryable_job = BookAnalysisJob.objects.create(
            book=analysis_job_failed.book,
            job_type='ocr',
            status='failed',
            retry_count=1,
            max_retries=3
        )
        
        retryable = BookAnalysisJob.objects.retryable()
        
        assert retryable_job in retryable
        assert analysis_job_failed not in retryable  # Exhausted retries


# ============================================================================
# CONTENT ACCESS TESTS
# ============================================================================

@pytest.mark.unit
class TestContentAccessModel:
    """Test ContentAccess model."""
    
    def test_create_content_access(self, content_access_course, student_user, course, admin_user):
        """Test creating content access."""
        assert content_access_course.user == student_user
        assert content_access_course.content_type == 'course'
        assert content_access_course.content_id == course.id
        assert content_access_course.permission == 'view'
        assert content_access_course.granted_by == admin_user
    
    def test_content_access_with_expiration(self, content_access_book):
        """Test time-limited access."""
        assert content_access_book.expires_at is not None
        assert content_access_book.expires_at > timezone.now()
    
    def test_content_access_is_valid(self, content_access_book, content_access_expired):
        """Test is_valid() checks expiration."""
        assert content_access_book.is_valid() is True
        assert content_access_expired.is_valid() is False
    
    def test_unique_user_content_access(self, content_access_course, student_user, course):
        """Test user + content_type + content_id must be unique."""
        with pytest.raises(IntegrityError):
            ContentAccess.objects.create(
                user=student_user,
                content_type='course',
                content_id=course.id,  # Duplicate
                permission='edit'
            )
    
    def test_content_access_permission_levels(self, student_user, course, admin_user):
        """Test different permission levels."""
        permissions = ['view', 'comment', 'edit']
        
        for i, perm in enumerate(permissions):
            access = ContentAccess.objects.create(
                user=student_user,
                content_type='course',
                content_id=course.id + i + 100,  # Different content IDs
                permission=perm,
                granted_by=admin_user
            )
            assert access.permission == perm
    
    def test_content_access_str_representation(self, content_access_course):
        """Test __str__ method."""
        access_str = str(content_access_course)
        assert content_access_course.user.name in access_str
        assert 'course' in access_str
        assert 'view' in access_str