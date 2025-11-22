"""
Content App Services

Business logic for PDF processing, OCR, and TOC extraction.

Note: These are synchronous implementations.
For production, move to Celery tasks (apps/content/tasks.py).
"""

import logging
from typing import Optional, Dict, Any, List
from pathlib import Path
from django.core.files.base import ContentFile
from django.utils import timezone

logger = logging.getLogger(__name__)


class PDFProcessingService:
    """
    Service for PDF processing operations.
    
    Methods:
    - extract_text_from_pdf: Extract text from all pages
    - extract_cover_image: Get first page as image
    - extract_toc: Parse table of contents
    - run_ocr: Optical character recognition
    """
    
    def __init__(self, book):
        """
        Initialize PDF processor.
        
        Args:
            book: Book model instance
        """
        self.book = book
        self.pdf_path = book.pdf_file.path if book.pdf_file else None
    
    def process_full_book(self) -> Dict[str, Any]:
        """
        Full book processing pipeline.
        
        Steps:
        1. Extract cover image
        2. Extract text from all pages
        3. Run OCR on scanned pages
        4. Extract TOC
        5. Generate keywords
        
        Returns:
            dict: Processing results with status and metadata
        """
        results = {
            'success': False,
            'cover_extracted': False,
            'pages_processed': 0,
            'toc_items': 0,
            'error': None
        }
        
        try:
            # Step 1: Extract cover
            cover_result = self.extract_cover_image()
            results['cover_extracted'] = cover_result['success']
            
            # Step 2: Extract pages
            pages_result = self.extract_all_pages()
            results['pages_processed'] = pages_result.get('pages_extracted', 0)
            
            # Step 3: Extract TOC
            toc_result = self.extract_toc()
            results['toc_items'] = toc_result.get('items_created', 0)
            
            # Step 4: Extract keywords (placeholder)
            keywords_result = self.extract_keywords()
            
            results['success'] = True
            logger.info(f"Book {self.book.id} processing completed successfully")
        
        except Exception as e:
            logger.error(f"Book {self.book.id} processing failed: {str(e)}", exc_info=True)
            results['error'] = str(e)
        
        return results
    
    def extract_cover_image(self) -> Dict[str, Any]:
        """
        Extract cover image from first page.
        
        Uses PyMuPDF (fitz) to render first page as image.
        
        Returns:
            dict: {'success': bool, 'image_path': str or None}
        """
        try:
            import fitz  # PyMuPDF
            
            # Open PDF
            doc = fitz.open(self.pdf_path)
            
            if len(doc) == 0:
                return {'success': False, 'error': 'PDF has no pages'}
            
            # Get first page
            first_page = doc[0]
            
            # Render page as image (300 DPI)
            pix = first_page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))
            
            # Convert to bytes
            img_bytes = pix.tobytes("png")
            
            # Save to model
            cover_filename = f"cover_{self.book.id}.png"
            self.book.cover_image.save(
                cover_filename,
                ContentFile(img_bytes),
                save=True
            )
            
            doc.close()
            
            logger.info(f"Cover image extracted for book {self.book.id}")
            return {'success': True, 'image_path': self.book.cover_image.url}
        
        except ImportError:
            logger.error("PyMuPDF (fitz) not installed. Install with: pip install PyMuPDF")
            return {'success': False, 'error': 'PyMuPDF not installed'}
        
        except Exception as e:
            logger.error(f"Cover extraction failed for book {self.book.id}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def extract_all_pages(self) -> Dict[str, Any]:
        """
        Extract text and images from all pages.
        
        Creates BookPage records with:
        - Page number
        - Page image (rendered)
        - Extracted text
        
        Returns:
            dict: {'pages_extracted': int, 'success': bool}
        """
        try:
            import fitz  # PyMuPDF
            from apps.content.models import BookPage
            
            doc = fitz.open(self.pdf_path)
            total_pages = len(doc)
            
            self.book.total_pages = total_pages
            self.book.save(update_fields=['total_pages'])
            
            pages_created = 0
            
            for page_num in range(total_pages):
                page = doc[page_num]
                
                # Extract text
                text = page.get_text()
                
                # Render page as image
                pix = page.get_pixmap(matrix=fitz.Matrix(150/72, 150/72))  # 150 DPI
                img_bytes = pix.tobytes("png")
                
                # Create BookPage
                book_page, created = BookPage.objects.get_or_create(
                    book=self.book,
                    page_number=page_num + 1,  # 1-indexed
                    defaults={
                        'extracted_text': text,
                        'ocr_status': 'completed' if text.strip() else 'pending'
                    }
                )
                
                # Save page image
                if created or not book_page.page_image:
                    page_filename = f"book_{self.book.id}_page_{page_num + 1}.png"
                    book_page.page_image.save(
                        page_filename,
                        ContentFile(img_bytes),
                        save=True
                    )
                
                # Update text if re-processing
                if not created and text.strip():
                    book_page.extracted_text = text
                    book_page.ocr_status = 'completed'
                    book_page.save(update_fields=['extracted_text', 'ocr_status'])
                
                pages_created += 1
                
                if (page_num + 1) % 10 == 0:
                    logger.debug(f"Processed {page_num + 1}/{total_pages} pages for book {self.book.id}")
            
            doc.close()
            
            logger.info(f"Extracted {pages_created} pages for book {self.book.id}")
            return {'pages_extracted': pages_created, 'success': True}
        
        except Exception as e:
            logger.error(f"Page extraction failed for book {self.book.id}: {str(e)}")
            return {'pages_extracted': 0, 'success': False, 'error': str(e)}
    
    def extract_toc(self) -> Dict[str, Any]:
        """
        Extract table of contents from PDF.
        
        Uses PDF's embedded TOC if available.
        Creates hierarchical BookTOCItem records.
        
        Returns:
            dict: {'items_created': int, 'success': bool}
        """
        try:
            import fitz  # PyMuPDF
            from apps.content.models import BookTOCItem
            from django.utils.text import slugify
            
            doc = fitz.open(self.pdf_path)
            toc = doc.get_toc()  # Returns [(level, title, page), ...]
            
            if not toc:
                logger.warning(f"No TOC found in book {self.book.id}")
                return {'items_created': 0, 'success': True, 'message': 'No TOC found'}
            
            items_created = 0
            parent_stack = {}  # Track parents at each level
            
            for idx, (level, title, page_num) in enumerate(toc):
                # Determine parent
                parent = None
                if level > 1:
                    parent = parent_stack.get(level - 1)
                
                # Determine end_page (next item's start page or last page)
                if idx + 1 < len(toc):
                    end_page = toc[idx + 1][2] - 1
                else:
                    end_page = doc.page_count
                
                # Create TOC item
                toc_item = BookTOCItem.objects.create(
                    book=self.book,
                    parent=parent,
                    level=level,
                    title=title,
                    start_page=page_num,
                    end_page=end_page,
                    slug=slugify(title),
                    order=idx
                )
                
                # Store in parent stack for future children
                parent_stack[level] = toc_item
                items_created += 1
            
            doc.close()
            
            logger.info(f"Extracted {items_created} TOC items for book {self.book.id}")
            return {'items_created': items_created, 'success': True}
        
        except Exception as e:
            logger.error(f"TOC extraction failed for book {self.book.id}: {str(e)}")
            return {'items_created': 0, 'success': False, 'error': str(e)}
    
    def run_ocr_on_page(self, page_number: int) -> Dict[str, Any]:
        """
        Run OCR on a specific page using Tesseract.
        
        Args:
            page_number: Page number (1-indexed)
        
        Returns:
            dict: {'success': bool, 'text': str, 'confidence': float}
        """
        try:
            from PIL import Image
            import pytesseract
            from apps.content.models import BookPage
            
            # Get page
            page = BookPage.objects.get(book=self.book, page_number=page_number)
            
            # Open page image
            img = Image.open(page.page_image.path)
            
            # Run OCR
            ocr_result = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
            
            # Extract text
            text = " ".join([
                word for word, conf in zip(ocr_result['text'], ocr_result['conf'])
                if int(conf) > 0
            ])
            
            # Calculate average confidence
            confidences = [int(conf) for conf in ocr_result['conf'] if int(conf) > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            # Update page
            page.extracted_text = text
            page.ocr_status = 'completed'
            page.ocr_confidence = avg_confidence / 100  # Normalize to 0-1
            page.ocr_completed_at = timezone.now()
            page.save()
            
            logger.info(
                f"OCR completed for book {self.book.id} page {page_number} "
                f"(confidence: {avg_confidence:.1f}%)"
            )
            
            return {
                'success': True,
                'text': text,
                'confidence': avg_confidence / 100
            }
        
        except ImportError:
            logger.error("pytesseract not installed. Install with: pip install pytesseract")
            return {'success': False, 'error': 'pytesseract not installed'}
        
        except Exception as e:
            logger.error(f"OCR failed for book {self.book.id} page {page_number}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def extract_keywords(self) -> Dict[str, Any]:
        """
        Extract keywords from book content.
        
        Placeholder for AI-based keyword extraction using Gemini.
        
        Returns:
            dict: {'keywords': List[str], 'success': bool}
        """
        # TODO: Implement with Gemini AI
        # For now, return placeholder
        return {'keywords': [], 'success': True, 'message': 'Not implemented yet'}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_book_text_content(book, start_page: Optional[int] = None, end_page: Optional[int] = None) -> str:
    """
    Get text content from book pages.
    
    Args:
        book: Book instance
        start_page: Starting page number (1-indexed, optional)
        end_page: Ending page number (1-indexed, optional)
    
    Returns:
        str: Combined text content
    """
    from apps.content.models import BookPage
    
    pages = BookPage.objects.filter(book=book)
    
    if start_page:
        pages = pages.filter(page_number__gte=start_page)
    if end_page:
        pages = pages.filter(page_number__lte=end_page)
    
    pages = pages.order_by('page_number')
    
    return "\n\n".join([page.extracted_text for page in pages if page.extracted_text])


def get_toc_text_content(toc_item) -> str:
    """
    Get text content for a specific TOC item (chapter/section).
    
    Args:
        toc_item: BookTOCItem instance
    
    Returns:
        str: Text content from pages in this TOC item's range
    """
    return get_book_text_content(
        toc_item.book,
        start_page=toc_item.start_page,
        end_page=toc_item.end_page
    )