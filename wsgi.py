"""Vercel entry point for the Django API and compiled React portal."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "backend"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.vercel_settings")

from django.core.wsgi import get_wsgi_application  # noqa: E402

application = get_wsgi_application()
