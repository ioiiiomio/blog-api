"""Shared settings for all environments."""

from pathlib import Path

from settings.conf import BLOG_ALLOWED_HOSTS, BLOG_SECRET_KEY

BASE_DIR: Path = Path(__file__).resolve().parent.parent
LOGS_DIR: Path = BASE_DIR / "logs"

SECRET_KEY: str = BLOG_SECRET_KEY
ALLOWED_HOSTS: list[str] = BLOG_ALLOWED_HOSTS

DJANGO_APPS: list[str] = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]
THIRD_PARTY_APPS: list[str] = [
    "rest_framework",
]
LOCAL_APPS: list[str] = [
    "apps.auths",
    "apps.blog",
]
INSTALLED_APPS: list[str] = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# Must be set before the first migration. App label is "auths", not "apps.auths".
AUTH_USER_MODEL: str = "auths.User"

MIDDLEWARE: list[str] = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF: str = "settings.urls"
WSGI_APPLICATION: str = "settings.wsgi.application"
ASGI_APPLICATION: str = "settings.asgi.application"

TEMPLATES: list[dict] = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

_PASSWORD_VALIDATION: str = "django.contrib.auth.password_validation"
AUTH_PASSWORD_VALIDATORS: list[dict[str, str]] = [
    {"NAME": f"{_PASSWORD_VALIDATION}.UserAttributeSimilarityValidator"},
    {"NAME": f"{_PASSWORD_VALIDATION}.MinimumLengthValidator"},
    {"NAME": f"{_PASSWORD_VALIDATION}.CommonPasswordValidator"},
    {"NAME": f"{_PASSWORD_VALIDATION}.NumericPasswordValidator"},
]

LANGUAGE_CODE: str = "en-us"
TIME_ZONE: str = "Asia/Almaty"
USE_I18N: bool = True
USE_TZ: bool = True

STATIC_URL: str = "static/"
STATIC_ROOT: Path = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD: str = "django.db.models.BigAutoField"

LOGS_DIR.mkdir(exist_ok=True)
LOGGING: dict = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {name}: {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOGS_DIR / "app.log",
            "maxBytes": 5 * 1024 * 1024,
            "backupCount": 5,
            "formatter": "verbose",
        },
    },
    "root": {"handlers": ["console", "file"], "level": "INFO"},
}
