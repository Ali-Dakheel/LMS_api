"""
ContentAccess Model
"""

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class ContentAccess(models.Model):
    """
    Granular access control for content with expiration.
    """
    
    CONTENT_TYPE_CHOICES = [
        ('course', 'Course'),
        ('path', 'Course Path'),
        ('module', 'Path Module'),
        ('book', 'Textbook'),
    ]
    
    PERMISSION_CHOICES = [
        ('view', 'View Only'),
        ('comment', 'View + Comment'),
        ('edit', 'Edit'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='content_access', db_index=True)
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPE_CHOICES, db_index=True)
    content_id = models.PositiveIntegerField(db_index=True)
    permission = models.CharField(max_length=20, choices=PERMISSION_CHOICES, default='view')
    
    # Time-limited
    expires_at = models.DateTimeField(null=True, blank=True)
    
    # Audit
    granted_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        related_name='granted_access', limit_choices_to={'role': 'admin'}
    )
    granted_at = models.DateTimeField(auto_now_add=True)
    reason = models.TextField(blank=True)
    
    class Meta:
        db_table = 'content_access'
        verbose_name = 'Content Access'
        verbose_name_plural = 'Content Access'
        unique_together = ['user', 'content_type', 'content_id']
        ordering = ['-granted_at']
        indexes = [
            models.Index(fields=['user', 'content_type']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"{self.user.name} → {self.content_type} #{self.content_id} ({self.permission})"
    
    def is_valid(self):
        from django.utils import timezone
        if self.expires_at and self.expires_at < timezone.now():
            return False
        return True