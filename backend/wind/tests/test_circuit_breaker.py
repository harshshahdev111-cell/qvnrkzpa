from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

import requests
from common.circuit_breaker import get_circuit_breaker
from django.test import SimpleTestCase, TestCase, override_settings
from integrations.elexon import ElexonClient
from pybreaker import STATE_CLOSED, STATE_OPEN, CircuitBreaker, CircuitBreakerError
from rest_framework.test import APIClient

from wind.models import Actual
from wind.services.ingestion import ImportFailure, import_history


@override_settings(
    ELEXON_RETRY_ATTEMPTS=1,
)
class CircuitBreakerTests(SimpleTestCase):
    def setUp(self):
        get_circuit_breaker.cache_clear()
        self.addCleanup(get_circuit_breaker.cache_clear)
        self.breaker = get_circuit_breaker(
            "test", 2, 30, ElexonClient._is_upstream_failure
        )
        self.operation = Mock(side_effect=requests.ConnectionError("offline"))
        self.clock = patch("pybreaker.datetime", wraps=datetime).start()
        self.addCleanup(patch.stopall)
        self.now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        self.clock.now.return_value = self.now

    def trip(self):
        for _ in range(2):
            with self.assertRaises(requests.ConnectionError):
                self.breaker.call(self.operation)
        self.assertEqual(self.breaker.current_state, STATE_OPEN)

    def test_uses_pybreaker_and_skips_network_until_cooldown(self):
        self.assertIsInstance(self.breaker, CircuitBreaker)
        self.trip()
        for seconds in [0, 29]:
            self.clock.now.return_value = self.now + timedelta(seconds=seconds)
            with self.assertRaises(CircuitBreakerError):
                self.breaker.call(self.operation)
        self.assertEqual(self.operation.call_count, 2)

    def test_successful_recovery_probe_closes(self):
        self.trip()
        self.clock.now.return_value = self.now + timedelta(seconds=30)
        self.assertEqual(self.breaker.call(lambda: ["recovered"]), ["recovered"])
        self.assertEqual(self.breaker.current_state, STATE_CLOSED)
        self.assertEqual(self.breaker.fail_counter, 0)

    def test_failed_recovery_probe_restarts_cooldown(self):
        self.trip()
        self.clock.now.return_value = self.now + timedelta(seconds=30)
        with self.assertRaises(requests.ConnectionError):
            self.breaker.call(self.operation)
        self.clock.now.return_value = self.now + timedelta(seconds=59)
        with self.assertRaises(CircuitBreakerError):
            self.breaker.call(self.operation)
        self.assertEqual(self.operation.call_count, 3)

    def test_success_resets_consecutive_failures(self):
        with self.assertRaises(requests.ConnectionError):
            self.breaker.call(self.operation)
        self.breaker.call(lambda: [])
        with self.assertRaises(requests.ConnectionError):
            self.breaker.call(self.operation)
        self.assertEqual(self.breaker.current_state, STATE_CLOSED)
        self.assertEqual(self.breaker.fail_counter, 1)

    def test_client_errors_excluded_and_server_errors_counted(self):
        for status in [400, 401, 404, 429, 500, 503]:
            response = requests.Response()
            response.status_code = status
            error = requests.HTTPError(response=response)
            self.assertEqual(
                self.breaker.is_system_error(error), status == 429 or status >= 500
            )
        self.assertTrue(self.breaker.is_system_error(requests.Timeout()))
        self.assertTrue(self.breaker.is_system_error(ValueError("invalid JSON")))
        response = requests.Response()
        response.status_code = 400
        for _ in range(3):
            with self.assertRaises(requests.HTTPError):
                self.breaker.call(
                    Mock(side_effect=requests.HTTPError(response=response))
                )
        self.assertEqual(self.breaker.fail_counter, 0)
        self.assertEqual(self.breaker.current_state, STATE_CLOSED)

    @override_settings(
        ELEXON_CIRCUIT_FAILURE_THRESHOLD=1, ELEXON_CIRCUIT_RECOVERY_TIMEOUT=60
    )
    def test_clients_share_library_breaker_and_skip_http(self):
        with patch("integrations.elexon.client.requests.get") as factory:
            factory.side_effect = requests.Timeout()
            first, second = ElexonClient(), ElexonClient()
            self.assertIs(first.breaker, second.breaker)
            self.assertIsInstance(first.breaker, CircuitBreaker)
            with self.assertRaises(requests.Timeout):
                first.get_rows("WINDFOR", {})
            with self.assertRaises(CircuitBreakerError):
                second.get_rows("FUELHH", {})
            factory.assert_called_once()


class OutageIsolationTests(TestCase):
    def test_open_library_breaker_preserves_data_and_dashboard(self):
        Actual.objects.create(
            start_time=datetime(2026, 1, 16, tzinfo=timezone.utc), generation=100
        )
        client = ElexonClient()
        client.get_response = Mock()
        client.get_response.side_effect = CircuitBreakerError("cooldown")
        with self.assertRaises(ImportFailure):
            import_history(client)
        self.assertEqual(Actual.objects.get().generation, 100)
        with patch(
            "integrations.elexon.client.requests.get",
            side_effect=AssertionError("Dashboard must not call upstream"),
        ):
            response = APIClient().get("/api/v1/dashboard/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["metrics"]["actual_periods"], 1)
