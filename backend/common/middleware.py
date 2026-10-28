"""Log API completion after rendering, including CSV and DRF errors."""

import logging
from time import perf_counter
from uuid import UUID, uuid4

from .logging import request_id_context

logger = logging.getLogger("common.requests")


class APIRequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path != "/api" and not request.path.startswith("/api/"):
            return self.get_response(request)
        try:
            request_id = str(UUID(request.headers.get("X-Request-ID", "")))
        except (ValueError, AttributeError):
            request_id = str(uuid4())
        request.request_id = request_id
        token = request_id_context.set(request_id)
        started = perf_counter()
        try:
            response = self.get_response(request)
            response["X-Request-ID"] = request_id
            status = response.status_code
            level = (
                logging.ERROR
                if status >= 500
                else logging.WARNING if status >= 400 else logging.INFO
            )
            match = request.resolver_match
            logger.log(
                level,
                "API request completed",
                extra={
                    "method": request.method,
                    # Route templates avoid logging identifiers or query values.
                    "route": match.route if match else "unresolved",
                    "status_code": status,
                    "duration_ms": round((perf_counter() - started) * 1000, 2),
                },
            )
            return response
        finally:
            request_id_context.reset(token)
