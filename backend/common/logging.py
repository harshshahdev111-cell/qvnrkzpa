"""Structured console logs with request correlation and a small field allowlist."""

import json
import logging
from contextvars import ContextVar
from datetime import datetime, timezone

request_id_context = ContextVar("request_id", default=None)


class JSONFormatter(logging.Formatter):
    def format(self, record):
        payload = {
            "timestamp": datetime.fromtimestamp(
                record.created, timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id_context.get()
            or getattr(getattr(record, "request", None), "request_id", None),
        }
        for field in ("method", "route", "status_code", "duration_ms"):
            if hasattr(record, field):
                payload[field] = getattr(record, field)
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=True)
