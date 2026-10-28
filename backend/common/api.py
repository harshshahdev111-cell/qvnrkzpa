"""Shared DRF response contract for all application endpoints."""

import logging
from http import HTTPStatus

from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView, exception_handler

logger = logging.getLogger(__name__)


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        logger.error(
            "Unhandled API exception", exc_info=(type(exc), exc, exc.__traceback__)
        )
        return Response({"detail": "An unexpected error occurred."}, status=500)
    return response


class StandardAPIView(APIView):
    """Wrap responses once, after DRF validation and exception handling."""

    success_message = "Request completed successfully."

    def finalize_response(self, request, response, *args, **kwargs):
        if isinstance(response, Response):
            success = response.status_code < 400
            payload = response.data
            message = self.success_message
            if not success:
                if isinstance(payload, dict) and "detail" in payload:
                    message = str(payload["detail"])
                else:
                    message = HTTPStatus(response.status_code).phrase
            response.data = {
                "success": success,
                "status_code": response.status_code,
                "message": message,
                "data": payload if success else None,
                "errors": None if success else payload,
            }
        return super().finalize_response(request, response, *args, **kwargs)


class APINotFoundView(StandardAPIView):
    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        raise NotFound("API endpoint not found.")
