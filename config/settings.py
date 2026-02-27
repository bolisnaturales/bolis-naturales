# config/settings.py
from pathlib import Path
import os
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# =========================
# SECURITY
# =========================
# ✅ Deja tu SECRET_KEY actual (NO la cambies aquí si ya la tienes en Render env)
SECRET_KEY = os.environ.get("SECRET_KEY", "DEJA_TU_SECRET_KEY_LOCAL_AQUI")

# ✅ En Render normalmente DEBUG debe ser False
DEBUG = os.environ.get("DEBUG", "False").lower() == "true"

# ✅ Deja tu ALLOWED_HOSTS actual (o usa env)
# Ejemplo: "bolisnaturales.shop,bolis-naturales.onrender.com"
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

# (Opcional recomendado en Render si lo usas)
CSRF_TRUSTED_ORIGINS = [
    "https://bolisnaturales.shop",
    "https://*.onrender.com",
]

# =========================
# APPS
# =========================
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # ✅ Cloudinary (MEDIA)
    "cloudinary_storage",
    "cloudinary",

    "productos",
]

# =========================
# MIDDLEWARE
# =========================
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",

    # ✅ Whitenoise para static en producción
    "whitenoise.middleware.WhiteNoiseMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

# =========================
# TEMPLATES
# =========================
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

WSGI_APPLICATION = "config.wsgi.application"

# =========================
# DATABASE
# =========================
DATABASE_URL = os.environ.get("DATABASE_URL", "")

if not DATABASE_URL:
    # LOCAL -> SQLite
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    # PRODUCCIÓN (Render) -> Postgres
    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
            ssl_require=True,
        )
    }

# =========================
# AUTH PASSWORD VALIDATION
# =========================
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# =========================
# I18N
# =========================
LANGUAGE_CODE = "es-mx"
TIME_ZONE = "America/Los_Angeles"
USE_I18N = True
USE_TZ = True

# =========================
# STATIC / MEDIA (✅ FIX DEFINITIVO)
# =========================
STATIC_URL = "/static/"

STATICFILES_DIRS = [
    BASE_DIR / "static",
]

STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"

# ✅ Django moderno: STORAGES (esto arregla tu problema)
# - staticfiles => Whitenoise
# - default => Cloudinary
STORAGES = {
    "default": {
        "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# ❌ NO uses MEDIA_ROOT con Cloudinary
# MEDIA_ROOT = BASE_DIR / "media"

# ❌ NO uses STATICFILES_STORAGE aquí porque ya está en STORAGES
# STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# ❌ NO uses DEFAULT_FILE_STORAGE aquí porque ya está en STORAGES
# DEFAULT_FILE_STORAGE = "cloudinary_storage.storage.MediaCloudinaryStorage"

# =========================
# DEFAULT PK FIELD
# =========================
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"