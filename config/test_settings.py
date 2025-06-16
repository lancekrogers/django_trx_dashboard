"""
Django settings for running tests.
Optimized for fast test execution.
"""

from .settings import *

# Test database configuration - use in-memory SQLite for speed
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
        'OPTIONS': {
            'init_command': 'PRAGMA foreign_keys=ON;',
        },
    }
}

# Disable migrations for faster tests
class DisableMigrations:
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None

MIGRATION_MODULES = DisableMigrations()

# Password hashers - use fast hasher for tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Cache - use local memory cache for tests
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Email - use console backend for tests
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Logging - reduce log level for tests
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'WARNING',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}

# Media files - use temporary directory for tests
MEDIA_ROOT = '/tmp/test_media'

# Static files - disable collection for tests
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# Debug - always False in tests
DEBUG = False

# Template debug
TEMPLATES[0]['OPTIONS']['debug'] = False

# Disable CSRF for API tests
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False

# Test-specific settings
TESTING = True

# Disable external API calls in tests
PORTFOLIO_API_ENABLED = False
BLOCKCHAIN_API_ENABLED = False

# Test user settings
TEST_USER_EMAIL = 'test@example.com'
TEST_USER_PASSWORD = 'testpass123'

# Performance settings for tests
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Time zone for tests
USE_TZ = True
TIME_ZONE = 'UTC'