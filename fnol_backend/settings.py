"""
Django settings for the FNOL Claims Processing project.

This is a DEV configuration meant for running the assessment locally /
demoing the project. For a real production deployment you would move
SECRET_KEY into an environment variable, set DEBUG=False, restrict
ALLOWED_HOSTS, and configure a production database (Postgres, etc.).
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# --- Security (DEV ONLY) -----------------------------------------------
SECRET_KEY = "dev-only-secret-key-change-me-before-any-real-deployment"
DEBUG = True
ALLOWED_HOSTS = ["*"]  # fine for local dev; restrict in production

# --- Applications --------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "rest_framework",   # Django REST Framework - powers the JSON API

    "claims",           # our FNOL claims-processing app
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "fnol_backend.urls"

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

WSGI_APPLICATION = "fnol_backend.wsgi.application"
ASGI_APPLICATION = "fnol_backend.asgi.application"

# --- Database --------------------------------------------------------------
# SQLite for zero-config local development. Swap to Postgres/MySQL for
# production by changing this dict (and installing the relevant driver).
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# --- Password validation (kept default, admin login uses this) -----------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- Internationalization ---------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

# --- Static files (CSS, JS) ---------------------------------------------
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- File upload handling ------------------------------------------------
# Keep small FNOL uploads fully in memory (no temp files written to disk).
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024  # 5 MB

# --- Django REST Framework ------------------------------------------------
REST_FRAMEWORK = {
    # No login/auth required for this demo API - it's a local assessment
    # project, not a multi-tenant public service. Add authentication here
    # (TokenAuthentication / JWT / etc.) before exposing this publicly.
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.MultiPartParser",
        "rest_framework.parsers.FormParser",
    ],
}
