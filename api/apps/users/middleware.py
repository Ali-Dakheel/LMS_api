"""
User Activity Tracking Middleware

Automatically tracks user activity on every authenticated request:
- Updates last_seen timestamp
- Records IP address
- Captures user agent

Usage:
    Add to MIDDLEWARE in settings.py:
    MIDDLEWARE = [
        ...
        'apps.users.middleware.UserActivityMiddleware',
    ]

Note: This middleware should be placed after authentication middleware.
"""

from typing import Optional, Callable
from django.http import HttpRequest, HttpResponse
from django.utils.deprecation import MiddlewareMixin


class UserActivityMiddleware(MiddlewareMixin):
    """
    Middleware to automatically track user activity.

    Updates user activity fields on every authenticated request,
    eliminating the need for manual update_last_seen() calls in views.
    """

    def process_request(self, request: HttpRequest) -> None:
        """
        Process incoming request and update user activity if authenticated.

        Args:
            request: HttpRequest object

        Side effects:
            Updates authenticated user's:
            - last_seen_at
            - last_ip_address
            - last_user_agent
        """
        if request.user.is_authenticated:
            # Extract client information
            ip_address = self._get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')

            # Update user activity
            request.user.update_last_seen(
                ip_address=ip_address,
                user_agent=user_agent
            )

    def _get_client_ip(self, request: HttpRequest) -> str:
        """
        Extract client IP address from request.

        Handles proxy headers (X-Forwarded-For) for accurate IP detection.

        Args:
            request: HttpRequest object

        Returns:
            str: Client IP address
        """
        # Check for proxy headers first
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # Take the first IP in the chain (original client)
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            # Fallback to REMOTE_ADDR
            ip = request.META.get('REMOTE_ADDR', '')

        return ip
