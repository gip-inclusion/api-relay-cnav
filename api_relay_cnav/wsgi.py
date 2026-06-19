import os

from django.core.wsgi import get_wsgi_application


if not os.environ.get("DJANGO_SETTINGS_MODULE"):
    raise RuntimeError("DJANGO_SETTINGS_MODULE environment variable is not set.")


application = get_wsgi_application()
