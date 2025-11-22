from .base import *

DEBUG = False
ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=lambda v: [s.strip() for s in v.split(',')])

SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Enforce HTTPS
SECURE_SSL_REDIRECT = True

# Disable debug toolbar
INSTALLED_APPS.remove('django_debug_toolbar')
MIDDLEWARE.remove('django_debug_toolbar.middleware.DebugToolbarMiddleware')