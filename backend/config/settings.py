import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
# Real process variables take precedence over a local .env file.
load_dotenv(BASE_DIR.parent / ".env", override=False)


def env_list(name, default=""):
    return [
        value.strip() for value in os.getenv(name, default).split(",") if value.strip()
    ]


SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    raise ImproperlyConfigured(
        "SECRET_KEY is required. Copy .env.example to .env and set a unique key."
    )
DEBUG = os.getenv("DEBUG", "0").lower() in {"1", "true", "yes"}
ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "localhost,127.0.0.1")
INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "wind",
]
MIDDLEWARE = [
    "common.middleware.APIRequestLoggingMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
]
ROOT_URLCONF = "config.urls"
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.getenv("DATABASE_PATH", str(BASE_DIR / "db.sqlite3")),
    }
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True
TIME_ZONE = "Europe/London"
CORS_EXPOSE_HEADERS = ["X-Request-ID"]
CORS_ALLOWED_ORIGINS = env_list(
    "CORS_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
)
ELEXON_BASE_URL = os.getenv(
    "ELEXON_BASE_URL", "https://data.elexon.co.uk/bmrs/api/v1/datasets"
).rstrip("/")
ELEXON_TIMEOUT = float(os.getenv("ELEXON_TIMEOUT", "90"))
ELEXON_RETRY_ATTEMPTS = int(os.getenv("ELEXON_RETRY_ATTEMPTS", "3"))
if ELEXON_RETRY_ATTEMPTS < 1:
    raise ImproperlyConfigured("ELEXON_RETRY_ATTEMPTS must be positive.")
REST_FRAMEWORK = {
    "EXCEPTION_HANDLER": "common.api.api_exception_handler",
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    "UNAUTHENTICATED_USER": None,
}
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
WHITENOISE_ROOT = BASE_DIR / "public"


LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
if LOG_LEVEL not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
    raise ImproperlyConfigured(
        "LOG_LEVEL must be DEBUG, INFO, WARNING, ERROR or CRITICAL."
    )
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"json": {"()": "common.logging.JSONFormatter"}},
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
            "stream": "ext://sys.stdout",
        }
    },
    "root": {"handlers": ["console"], "level": LOG_LEVEL},
    "loggers": {
        "common": {"handlers": ["console"], "level": LOG_LEVEL, "propagate": False},
        "integrations": {
            "handlers": ["console"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "wind": {"handlers": ["console"], "level": LOG_LEVEL, "propagate": False},
        "django": {"handlers": ["console"], "level": "WARNING", "propagate": False},
    },
}

ELEXON_CIRCUIT_FAILURE_THRESHOLD = int(
    os.getenv("ELEXON_CIRCUIT_FAILURE_THRESHOLD", "3")
)
ELEXON_CIRCUIT_RECOVERY_TIMEOUT = float(
    os.getenv("ELEXON_CIRCUIT_RECOVERY_TIMEOUT", "60")
)
if ELEXON_CIRCUIT_FAILURE_THRESHOLD < 1 or ELEXON_CIRCUIT_RECOVERY_TIMEOUT <= 0:
    raise ImproperlyConfigured("Elexon circuit breaker settings must be positive.")
