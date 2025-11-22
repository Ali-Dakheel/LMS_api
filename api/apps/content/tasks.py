"""
Celery Tasks for Content App

Async tasks for:
- PDF processing
- OCR
- TOC extraction

Note: Requires Celery setup (Phase 8).
For now, these are stubs.
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def process_book_pdf(book_id: int, job_id: int) -> Dict[str, Any]:
    """
    Celery task: Process book PDF (full pipeline).
    
    TODO: Convert to @shared_task when Celery is configured.
    
    Args:
        book_id: Book primary key
        job_id: BookAnalysisJob primary key
    
    Returns:
        dict: Processing results
    """
    from apps.content.models import Book, BookAnalysisJob
    from apps.content.services import PDFProcessingService
    from django.utils import timezone
    
    try:
        book = Book.objects.get(id=book_id)
        job = BookAnalysisJob.objects.get(id=job_id)
        
        # Update job status
        job.status = 'processing'
        job.started_at = timezone.now()
        job.save(update_fields=['status', 'started_at'])
        
        # Update book status
        book.status = 'processing'
        book.save(update_fields=['status'])
        
        # Process book
        processor = PDFProcessingService(book)
        results = processor.process_full_book()
        
        # Update job
        if results['success']:
            job.status = 'completed'
            job.progress_percent = 100
            job.processed_items = job.total_items
        else:
            job.status = 'failed'
            job.error_message = results.get('error', 'Unknown error')
        
        job.completed_at = timezone.now()
        job.save()
        
        return results
    
    except Exception as e:
        logger.error(f"Book processing task failed: {str(e)}", exc_info=True)
        
        # Update job as failed
        try:
            job = BookAnalysisJob.objects.get(id=job_id)
            job.status = 'failed'
            job.error_message = str(e)
            job.completed_at = timezone.now()
            job.save()
        except:
            pass
        
        return {'success': False, 'error': str(e)}


def run_ocr_on_page(book_id: int, page_number: int) -> Dict[str, Any]:
    """
    Celery task: Run OCR on a single page.
    
    TODO: Convert to @shared_task when Celery is configured.
    
    Args:
        book_id: Book primary key
        page_number: Page number (1-indexed)
    
    Returns:
        dict: OCR results
    """
    from apps.content.models import Book
    from apps.content.services import PDFProcessingService
    
    try:
        book = Book.objects.get(id=book_id)
        processor = PDFProcessingService(book)
        
        return processor.run_ocr_on_page(page_number)
    
    except Exception as e:
        logger.error(f"OCR task failed: {str(e)}", exc_info=True)
        return {'success': False, 'error': str(e)}