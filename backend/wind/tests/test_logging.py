import json
import logging
from unittest.mock import patch
from uuid import UUID, uuid4

from common.logging import JSONFormatter, request_id_context
from django.test import TestCase
from rest_framework.test import APIClient


class RequestLoggingTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_success_and_request_id_propagation(self):
        correlation = str(uuid4())
        with self.assertLogs("common.requests", level="INFO") as logs:
            response = self.client.get(
                "/api/v1/status/?token=private-value",
                HTTP_X_REQUEST_ID=correlation,
                HTTP_AUTHORIZATION="secret-header",
            )
        self.assertEqual(response["X-Request-ID"], correlation)
        record = logs.records[0]
        self.assertEqual(record.status_code, 200)
        self.assertEqual(record.method, "GET")
        self.assertGreaterEqual(record.duration_ms, 0)
        self.assertNotIn("private-value", str(record.__dict__))
        self.assertNotIn("secret-header", str(record.__dict__))
        self.assertIsNone(request_id_context.get())

    def test_invalid_id_is_replaced_and_not_reused(self):
        first = self.client.get(
            "/api/v1/status/", HTTP_X_REQUEST_ID="invalid\r\ninjection"
        )
        second = self.client.get("/api/v1/status/")
        UUID(first["X-Request-ID"])
        UUID(second["X-Request-ID"])
        self.assertNotEqual(first["X-Request-ID"], second["X-Request-ID"])

    def test_client_and_server_error_log_levels(self):
        with self.assertLogs("common.requests", level="WARNING") as logs:
            response = self.client.get("/api/v1/dashboard/?cutoff=invalid")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(logs.records[0].levelno, logging.WARNING)
        correlation = str(uuid4())
        with patch(
            "wind.api.v1.views.analyze", side_effect=RuntimeError("test exception")
        ):
            with self.assertLogs("common", level="ERROR") as logs:
                response = self.client.get(
                    "/api/v1/dashboard/", HTTP_X_REQUEST_ID=correlation
                )
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response["X-Request-ID"], correlation)
        self.assertTrue(any(record.exc_info for record in logs.records))
        self.assertTrue(
            any(getattr(record, "status_code", None) == 500 for record in logs.records)
        )

    def test_formatter_is_valid_json_and_context_does_not_leak(self):
        formatter = JSONFormatter()
        record = logging.LogRecord(
            "test", logging.INFO, "", 0, "API request completed", (), None
        )
        token = request_id_context.set("request-one")
        try:
            self.assertEqual(
                json.loads(formatter.format(record))["request_id"], "request-one"
            )
        finally:
            request_id_context.reset(token)
        self.assertIsNone(json.loads(formatter.format(record))["request_id"])

    def test_static_requests_are_not_logged(self):
        with self.assertNoLogs("common.requests", level="INFO"):
            self.client.get("/")
