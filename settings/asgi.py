import os

from django.core.asgi import get_asgi_application

from settings.conf import ENV_ID


assert ENV_ID, "BLOG_ENV_ID is not set in settings/.env"

os.environ.setdefault("DJANGO_SETTINGS_MODULE", f"settings.env.{ENV_ID}")

application = get_asgi_application()
