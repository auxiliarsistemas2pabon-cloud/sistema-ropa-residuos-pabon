"""
Configuración común a todos los entornos. local.py y production.py
la importan con `from .base import *` y solo sobrescriben lo que cambia.
"""
import os
from datetime import time, timedelta
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
    "rest_framework",
    "corsheaders",
    "axes",
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
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "simple_history.middleware.HistoryRequestMiddleware",
    # Último: convierte el bloqueo por intentos fallidos en la respuesta de
    # core.seguridad.respuesta_bloqueo.
    "axes.middleware.AxesMiddleware",
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

# axes va primero: rechaza el intento antes de comprobar la contraseña si la
# cuenta está bloqueada.
AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",
    "django.contrib.auth.backends.ModelBackend",
]

# Protocolo de seguridad, A3: mínimo 10 caracteres. Las contraseñas solo las
# asigna la Administradora (Catálogos), y la regla vale también ahí.
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 10},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Protocolo de seguridad, A2: 5 intentos fallidos bloquean la cuenta 15
# minutos, en la pantalla de ingreso de Django y en /api/auth/login/. Se
# bloquea por usuario (no por IP): en la clínica todos salen a internet por
# la misma IP y bloquearla dejaría afuera a todo el personal.
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = timedelta(minutes=15)
AXES_LOCKOUT_PARAMETERS = ["username"]
# axes recomienda sumar la IP (W006), pero bloquear por IP con este mismo
# límite dejaría sin acceso a toda una sede cada vez que alguien se equivoque
# cinco veces. Cada intento fallido igual queda registrado con su IP.
SILENCED_SYSTEM_CHECKS = ["axes.W006"]
AXES_RESET_ON_SUCCESS = True
# Los intentos durante el bloqueo no lo alargan: siempre son 15 minutos.
AXES_RESET_COOL_OFF_ON_FAILURE_DURING_LOCKOUT = False
# Cada intento fallido queda con IP y hora (AccessFailureLog), no solo el contador.
AXES_ENABLE_ACCESS_FAILURE_LOG = True
AXES_LOCKOUT_CALLABLE = "core.seguridad.respuesta_bloqueo"
AXES_CLIENT_IP_CALLABLE = "core.seguridad.ip_del_cliente"
# Solo detrás de un proxy propio (Caddy en producción) se puede creer en
# X-Forwarded-For; de lo contrario cualquiera inventaría su IP.
CONFIAR_EN_X_FORWARDED_FOR = False

LANGUAGE_CODE = "es"
TIME_ZONE = "America/Bogota"
USE_I18N = True
USE_TZ = True

# El español localiza los decimales con coma (5,30); el resto de la app usa
# punto (JS, mensajes, formularios con localize=False) — se homogeniza aquí.
FORMAT_MODULE_PATH = ["config.formats"]

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

# API REST (DRF) para el futuro frontend React. Autenticación por sesión
# (no JWT) para reutilizar el cierre por inactividad de arriba y para que
# las descargas de Excel sigan funcionando con un <a href> normal.
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 25,
}

# CORS/CSRF para un frontend servido desde otro origen (p.ej. Vite en
# desarrollo). Nunca CORS_ALLOW_ALL_ORIGINS=True: es incompatible con
# credenciales (cookies) y anularía la protección de sesión.
CORS_ALLOWED_ORIGINS = [o.strip() for o in os.environ.get("CORS_ALLOWED_ORIGINS", "").split(",") if o.strip()]
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = [o.strip() for o in os.environ.get("CSRF_TRUSTED_ORIGINS", "").split(",") if o.strip()]

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# Respaldos (RNF-15: diario, retención mínima de 30 días).
# El destino se configura en STORAGES["dbbackup"] (arriba).
DBBACKUP_CLEANUP_KEEP = 35
DBBACKUP_CLEANUP_KEEP_MEDIA = 35
DBBACKUP_FILENAME_TEMPLATE = "{datetime}-{databasename}.{extension}"
DBBACKUP_DATE_FORMAT = "%Y%m%d-%H%M%S"

# Protocolo de seguridad, A5 (ver core/management/commands/respaldo_diario.py).
# Vacíos = desactivado, como en desarrollo; `check --deploy` avisa si faltan.
# - Cifrado con la llave PÚBLICA GPG de la clínica: la privada nunca está en el
#   servidor, así que quien se lleve el servidor no puede abrir las copias.
RESPALDO_GPG_DESTINATARIO = os.environ.get("RESPALDO_GPG_DESTINATARIO", "")
RESPALDO_GPG_LLAVE_PUBLICA = os.environ.get("RESPALDO_GPG_LLAVE_PUBLICA", "")
DBBACKUP_GPG_RECIPIENT = RESPALDO_GPG_DESTINATARIO or None
# - Copia de cada respaldo en un disco montado fuera del servidor (NAS de otra
#   sede, carpeta sincronizada con la nube...). Ahí se conservan las últimas
#   DBBACKUP_CLEANUP_KEEP copias más la última de cada uno de los 12 meses previos.
RESPALDO_COPIA_EXTERNA_DIR = os.environ.get("RESPALDO_COPIA_EXTERNA_DIR", "")
RESPALDO_MESES_CONSERVADOS = 12
# - A quién se avisa por correo si un respaldo falla.
RESPALDO_AVISO_CORREOS = [c.strip() for c in os.environ.get("RESPALDO_AVISO_CORREOS", "").split(",") if c.strip()]

# Correo saliente (avisos de respaldo fallido). En desarrollo, local.py lo
# manda a la consola.
EMAIL_HOST = os.environ.get("EMAIL_HOST", "localhost")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT") or 587)
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "true").lower() == "true"
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", EMAIL_HOST_USER or "webmaster@localhost")
SERVER_EMAIL = DEFAULT_FROM_EMAIL

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
