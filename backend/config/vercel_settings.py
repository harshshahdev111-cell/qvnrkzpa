"""Read-only historical pilot deployment; imports still run locally."""

import os

from . import settings as base
from .settings import *  # noqa: F403

DEBUG = False
WSGI_APPLICATION = "config.wsgi.application"
ALLOWED_HOSTS = list(
    dict.fromkeys(
        [
            *base.ALLOWED_HOSTS,
            ".vercel.app",
            os.environ.get("VERCEL_URL", ""),
            os.environ.get("VERCEL_PROJECT_PRODUCTION_URL", ""),
        ]
    )
)
ALLOWED_HOSTS = [host for host in ALLOWED_HOSTS if host]
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": f"file:{(base.BASE_DIR / 'data' / 'pilot.sqlite3').as_posix()}?mode=ro",
        "OPTIONS": {"uri": True},
    }
}
# Vite uses /static/ for this deployment. Vercel's Django builder collects these
# files and serves them from its CDN; Django serves the HTML entry point.
STATICFILES_DIRS = [base.BASE_DIR / "public"]
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
