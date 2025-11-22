"""
Content App Managers
"""

from django.db import models
from django.db.models import Prefetch, Q, Count


class BookQuerySet(models.QuerySet):
    def published_only(self):
        return self.filter(is_published=True)
    
    def completed_only(self):
        return self.filter(status='completed')
    
    def with_pages(self):
        return self.prefetch_related('pages')
    
    def with_toc(self):
        return self.prefetch_related('toc_items')
    
    def with_all_relations(self):
        return self.select_related().with_pages().with_toc().prefetch_related('courses')
    
    def for_course(self, course):
        return self.filter(courses=course)
    
    def by_status(self, status):
        return self.filter(status=status)


class BookManager(models.Manager):
    def get_queryset(self):
        return BookQuerySet(self.model, using=self._db)
    
    def published_only(self):
        return self.get_queryset().published_only()
    
    def completed_only(self):
        return self.get_queryset().completed_only()
    
    def for_course(self, course):
        return self.get_queryset().for_course(course)


class BookAnalysisJobQuerySet(models.QuerySet):
    def pending(self):
        return self.filter(status__in=['queued', 'processing'])
    
    def failed(self):
        return self.filter(status='failed')
    
    def retryable(self):
        return self.filter(
            status__in=['failed', 'retrying'],
            retry_count__lt=models.F('max_retries')
        )
    
    def for_book(self, book):
        return self.filter(book=book)


class BookAnalysisJobManager(models.Manager):
    def get_queryset(self):
        return BookAnalysisJobQuerySet(self.model, using=self._db)
    
    def pending(self):
        return self.get_queryset().pending()
    
    def failed(self):
        return self.get_queryset().failed()
    
    def retryable(self):
        return self.get_queryset().retryable()