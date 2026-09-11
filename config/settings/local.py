import os

from .base import *  # noqa: F401,F403

DEBUG = True

SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY", "django-insecure-dev-only-not-for-production-6f1e9c2a"
)

ALLOWED_HOSTS = ["*"]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Origen por defecto del servidor de desarrollo de Vite (el futuro frontend
# React), para que las cookies de sesión viajen entre los dos puertos.
CORS_ALLOWED_ORIGINS = CORS_ALLOWED_ORIGINS or ["http://localhost:5173"]
CSRF_TRUSTED_ORIGINS = CSRF_TRUSTED_ORIGINS or ["http://localhost:5173"]

# WhiteNoise sirve los estáticos con los finders, sin necesidad de collectstatic
# ni del directorio staticfiles/ en desarrollo.
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = True
