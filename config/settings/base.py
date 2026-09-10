"""
Configuración común a todos los entornos. local.py y production.py
la importan con `from .base import *` y solo sobrescriben lo que cambia.
"""
import os
from datetime import time
from decimal import Decimal
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # terceros
    "simple_history",
    "constance",
    "django_filters",
    "django_tables2",
    "crispy_forms",
    "crispy_bootstrap5",
    "dbbackup",
    # propias
    "core",
    "movimientos",
    "ropa",
    "residuos",
    "reportes",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "simple_history.middleware.HistoryRequestMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "clinica_pabon"),
        "USER": os.environ.get("POSTGRES_USER", "clinica_pabon"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "clinica_pabon"),
        "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
    }
}

AUTH_USER_MODEL = "core.Usuario"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "es"
TIME_ZONE = "America/Bogota"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    "dbbackup": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
        "OPTIONS": {"location": str(BASE_DIR / "backups")},
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Cierre de sesión automático a los 30 minutos de inactividad (RNF-10).
SESSION_COOKIE_AGE = 1800
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "panel_principal"
LOGOUT_REDIRECT_URL = "login"

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# Respaldos (RNF-15: diario, retención mínima de 30 días).
# El destino se configura en STORAGES["dbbackup"] (arriba).
DBBACKUP_CLEANUP_KEEP = 35
DBBACKUP_CLEANUP_KEEP_MEDIA = 35
DBBACKUP_FILENAME_TEMPLATE = "{datetime}-{databasename}.{extension}"
DBBACKUP_DATE_FORMAT = "%Y%m%d-%H%M%S"

# Parámetros editables desde el admin sin desarrollo (capítulo 13 del prompt de desarrollo).
CONSTANCE_BACKEND = "constance.backends.database.DatabaseBackend"
CONSTANCE_CONFIG = {
    "VENTANA_EDICION_USUARIO_MINUTOS": (
        60,
        "Minutos que el perfil Usuario puede editar su propio registro después de crearlo (6.9).",
    ),
    "JORNADA_MANANA_INICIO": (
        time(7, 0),
        "Institucional por defecto: inicio de jornada mañana (respaldo si la sede/proceso no tiene ConfiguracionJornada propia).",
    ),
    "JORNADA_MANANA_FIN": (
        time(12, 59),
        "Institucional por defecto: fin de jornada mañana.",
    ),
    "JORNADA_TARDE_INICIO": (
        time(13, 0),
        "Institucional por defecto: inicio de jornada tarde.",
    ),
    "JORNADA_TARDE_FIN": (
        time(19, 0),
        "Institucional por defecto: fin de jornada tarde.",
    ),
    "BLOQUEO_DIFERENCIA_ACTIVO": (
        False,
        "Si está activo, una diferencia de peso mayor al umbral impide cerrar el movimiento (6.7). Desactivado por defecto.",
    ),
    "UMBRAL_DIFERENCIA_KG": (
        Decimal("0"),
        "Umbral de diferencia en kilogramos que activa el bloqueo, cuando BLOQUEO_DIFERENCIA_ACTIVO está activo.",
    ),
    "UMBRAL_DIFERENCIA_PORCENTAJE": (
        Decimal("0"),
        "Umbral de diferencia en porcentaje que activa el bloqueo.",
    ),
}
CONSTANCE_CONFIG_FIELDSETS = {
    "Jornadas (respaldo institucional)": (
        "JORNADA_MANANA_INICIO", "JORNADA_MANANA_FIN", "JORNADA_TARDE_INICIO", "JORNADA_TARDE_FIN",
    ),
    "Edición y validación": (
        "VENTANA_EDICION_USUARIO_MINUTOS", "BLOQUEO_DIFERENCIA_ACTIVO",
        "UMBRAL_DIFERENCIA_KG", "UMBRAL_DIFERENCIA_PORCENTAJE",
    ),
}
