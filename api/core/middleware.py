import time
import logging
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)

class SecurityHeadersMiddleware(MiddlewareMixin):
    """Add OWASP-compliant security headers."""
    
    def process_response(self, request, response):
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'SAMEORIGIN'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Cross-Origin-Opener-Policy'] = 'same-origin'
        response['Cross-Origin-Resource-Policy'] = 'same-origin'
        
        # HSTS only if HTTPS
        if request.is_secure() or request.META.get('HTTP_X_FORWARDED_PROTO') == 'https':
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        return response

class RequestLoggingMiddleware(MiddlewareMixin):
    """Log all API requests with performance metrics."""
    
    def process_request(self, request):
        request.start_time = time.time()
    
    def process_response(self, request, response):
        if not hasattr(request, 'start_time'):
            return response
        
        duration = time.time() - request.start_time
        user_id = getattr(request.user, 'id', 'Anonymous')
        
        # Log slow requests (>1s)
        if duration > 1.0:
            logger.warning(
                f"SLOW_REQUEST | {request.method} {request.path} "
                f"| Status: {response.status_code} | Duration: {duration:.2f}s | User: {user_id}"
            )
        else:
            logger.info(
                f"{request.method} {request.path} "
                f"| Status: {response.status_code} | Duration: {duration:.2f}s | User: {user_id}"
            )
        
        return response