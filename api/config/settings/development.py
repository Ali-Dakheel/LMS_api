from .base import *

DEBUG = True
ALLOWED_HOSTS = ['*']

INSTALLED_APPS += [
    'django_extensions',
    'debug_toolbar',
]

MIDDLEWARE += [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]

INTERNAL_IPS = ['127.0.0.1']

# Development-specific settings
LOGGING['loggers']['apps']['level'] = 'DEBUG'