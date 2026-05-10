"""
Test-specific settings for HospFlow
"""
from .settings import *  # noqa

DEBUG = True
SECRET_KEY = "test-secret-key-not-for-production-use-only"

# Use SQLite for faster tests
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Disable password hashing for faster tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Disable Celery in tests
CELERY_TASK_ALWAYS_EAGER = True

# Use console email backend
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
