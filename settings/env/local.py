from settings.base import *

DEBUG: bool = True

DATABASES: dict = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}
