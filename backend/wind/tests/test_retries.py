from unittest.mock import Mock, patch

import requests
from common.circuit_breaker import get_circuit_breaker
from django.test import SimpleTestCase, override_settings
from integrations.elexon import ElexonClient
from pybreaker import CircuitBreakerError


@override_settings(ELEXON_RETRY_ATTEMPTS=3)
class RetryTests(SimpleTestCase):
    def setUp(self):
        get_circuit_breaker.cache_clear()
        self.addCleanup(get_circuit_breaker.cache_clear)
        self.transport = patch("integrations.elexon.client.requests.get").start()
        self.addCleanup(patch.stopall)
        self.client = ElexonClient()
        self.client.retrying.sleep = Mock()
        self.transport.return_value.json.return_value = [{"generation": 100}]

    def test_repeated_calls_always_fetch_upstream(self):
        self.client.get_rows("WINDFOR", {})
        self.client.get_rows("WINDFOR", {})
        self.assertEqual(self.transport.call_count, 2)

    def test_retry_attempts_bounded_and_breaker_counts_once(self):
        self.transport.side_effect = requests.Timeout()
        with self.assertRaises(requests.Timeout):
            self.client.get_rows("WINDFOR", {})
        self.assertEqual(self.transport.call_count, 3)
        self.assertEqual(self.client.breaker.fail_counter, 1)

    def test_transient_failure_recovers(self):
        response = self.transport.return_value
        self.transport.side_effect = [requests.Timeout(), response]
        self.assertEqual(self.client.get_rows("WINDFOR", {}), [{"generation": 100}])
        self.assertEqual(self.transport.call_count, 2)
        self.assertEqual(self.client.breaker.fail_counter, 0)

    def test_open_circuit_skips_network_and_retries(self):
        self.client.breaker.open()
        with self.assertRaises(CircuitBreakerError):
            self.client.get_rows("WINDFOR", {})
        self.transport.assert_not_called()
        self.client.retrying.sleep.assert_not_called()

    def test_client_error_is_not_retried(self):
        response = requests.Response()
        response.status_code = 400
        self.transport.side_effect = requests.HTTPError(response=response)
        with self.assertRaises(requests.HTTPError):
            self.client.get_rows("WINDFOR", {})
        self.transport.assert_called_once()
        self.assertEqual(self.client.breaker.fail_counter, 0)
