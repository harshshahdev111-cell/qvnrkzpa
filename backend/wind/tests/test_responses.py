from unittest.mock import patch

from django.test import SimpleTestCase, override_settings
from integrations.elexon import ElexonClient
from rest_framework.test import APIClient


class ResponseEnvelopeTests(SimpleTestCase):
    def setUp(self):
        self.client = APIClient()

    def assert_envelope(self, response, code):
        self.assertEqual(response.status_code, code)
        payload = response.json()
        self.assertEqual(
            set(payload), {"success", "status_code", "message", "data", "errors"}
        )
        self.assertEqual(payload["status_code"], code)
        self.assertFalse(payload["success"])
        self.assertIsNone(payload["data"])
        self.assertTrue(payload["message"])
        self.assertIsNotNone(payload["errors"])
        return payload

    def test_validation_error_contract(self):
        payload = self.assert_envelope(
            self.client.get("/api/v1/dashboard/?cutoff=no"), 400
        )
        self.assertIn("cutoff", payload["errors"])

    def test_unknown_route_and_method_contract(self):
        self.assert_envelope(self.client.get("/api/v1/missing/"), 404)
        self.assert_envelope(
            self.client.post("/api/v1/dashboard/", {}, format="json"), 405
        )

    def test_unexpected_error_is_sanitized(self):
        with patch(
            "wind.api.v1.views.analyze",
            side_effect=RuntimeError("private internal detail"),
        ):
            with self.assertLogs("common.api", level="ERROR"):
                response = self.client.get("/api/v1/dashboard/")
        payload = self.assert_envelope(response, 500)
        self.assertNotIn("private internal detail", str(payload))

    def test_csv_validation_error(self):
        response = self.client.get("/api/v1/dashboard/?format=csv&cutoff=no")
        self.assertEqual(response.status_code, 400)
        self.assertIn("text/csv", response["Content-Type"])
        self.assertIn("Bad Request", response.content.decode())

    @override_settings(
        ELEXON_BASE_URL="https://example.test/datasets",
        ELEXON_TIMEOUT=12,
        ELEXON_RETRY_ATTEMPTS=2,
    )
    def test_upstream_client_uses_environment_settings(self):
        with patch("integrations.elexon.client.requests.get") as factory:
            factory.return_value.json.return_value = []
            client = ElexonClient()
            self.assertEqual(client.get_rows("WINDFOR", {"key": "value"}), [])
            factory.assert_called_once_with(
                "https://example.test/datasets/WINDFOR/stream",
                params={"key": "value"},
                timeout=12,
            )
