"""Contracts at the external API boundary, without network requests."""

from datetime import date, datetime, timezone
from unittest.mock import Mock, patch

from django.test import SimpleTestCase, override_settings
from integrations.elexon import ElexonClient, ElexonService
from integrations.elexon.utils import ProviderResponse, generation, timestamp


class ElexonIntegrationTests(SimpleTestCase):
    @override_settings(ELEXON_BASE_URL="https://example.test/datasets/")
    @patch("integrations.elexon.client.requests.get")
    def test_endpoint_parameters(self, get):
        get.return_value.json.return_value = []
        get.return_value.status_code = 200
        get.return_value.headers = {"X-Source": "elexon"}
        day = datetime(2026, 1, 1, tzinfo=timezone.utc)
        client = ElexonClient()
        response = client.get_wind_forecasts(day, day)
        self.assertEqual(response, ProviderResponse(200, [], {"X-Source": "elexon"}))
        get.assert_called_with(
            "https://example.test/datasets/WINDFOR/stream",
            params={
                "publishDateTimeFrom": day.isoformat(),
                "publishDateTimeTo": day.isoformat(),
            },
            timeout=client.timeout,
        )
        client.get_wind_actuals(date(2026, 1, 2))
        get.assert_called_with(
            "https://example.test/datasets/FUELHH/stream",
            params={
                "settlementDateFrom": "2026-01-02",
                "settlementDateTo": "2026-01-02",
                "fuelType": "WIND",
            },
            timeout=client.timeout,
        )

    def test_service_normalizes_forecasts(self):
        client = Mock()
        client.get_wind_forecasts.return_value = ProviderResponse(
            200,
            [
                {
                    "startTime": "2026-01-02T00:00:00Z",
                    "publishTime": "2026-01-01T09:00:00",
                    "generation": "0",
                }
            ],
            {},
        )
        result = ElexonService(client).get_wind_forecasts("from", "to")
        client.get_wind_forecasts.assert_called_once_with("from", "to")
        self.assertEqual(
            result,
            [
                {
                    "start_time": datetime(2026, 1, 2, tzinfo=timezone.utc),
                    "publish_time": datetime(2026, 1, 1, 9, tzinfo=timezone.utc),
                    "generation": 0.0,
                }
            ],
        )

    def test_actuals_filter_other_fuels_and_allow_missing_publication(self):
        result = ElexonService.parse_wind_actuals(
            [
                {"fuelType": "GAS"},
                {
                    "fuelType": "WIND",
                    "startTime": "2026-01-02T00:00:00Z",
                    "generation": 10,
                },
            ]
        )
        self.assertEqual(len(result), 1)
        self.assertIsNone(result[0]["publish_time"])

    def test_malformed_rows_are_rejected(self):
        for parser in [
            ElexonService.parse_wind_forecasts,
            ElexonService.parse_wind_actuals,
        ]:
            for rows in [{}, [None], ["invalid"]]:
                with self.subTest(parser=parser.__name__, rows=rows):
                    with self.assertRaises(ValueError):
                        parser(rows)

    def test_invalid_measurements_and_timestamps_are_rejected(self):
        for value in [True, None, "nan", "inf", -1, {}]:
            with self.subTest(generation=value):
                with self.assertRaises(ValueError):
                    generation(value, "forecast")
        for value in [None, 123, "invalid", "2026-99-99T00:00:00"]:
            with self.subTest(timestamp=value):
                with self.assertRaises(ValueError):
                    timestamp(value)
