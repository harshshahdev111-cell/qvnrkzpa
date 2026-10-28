from datetime import datetime, timezone
from unittest.mock import Mock

from django.test import TestCase
from integrations.elexon import ElexonClient
from integrations.elexon.utils import ProviderResponse
from rest_framework.test import APIClient

from wind.models import Actual, Forecast, ImportRun
from wind.services.ingestion import ImportFailure, import_history


class IngestionTests(TestCase):
    def test_failed_import_does_not_change_existing_data(self):
        target = datetime(2026, 1, 2, tzinfo=timezone.utc)
        Actual.objects.create(start_time=target, generation=10)
        client = ElexonClient()
        client.get_response = Mock()
        client.get_response.side_effect = ValueError("Invalid upstream payload")
        with self.assertRaises(ImportFailure):
            import_history(client)
        self.assertEqual(Actual.objects.get().generation, 10)
        self.assertFalse(Forecast.objects.exists())
        self.assertFalse(ImportRun.objects.exists())

    def test_import_is_idempotent_and_selects_latest_actual_revision(self):
        client = ElexonClient()
        client.get_response = Mock()

        def rows(dataset, **kwargs):
            if dataset == "WINDFOR":
                return [
                    {
                        "startTime": "2026-01-02T00:00:00Z",
                        "publishTime": "2026-01-01T09:00:00Z",
                        "generation": 15,
                    }
                ]
            return [
                {
                    "fuelType": "WIND",
                    "startTime": "2026-01-02T00:00:00Z",
                    "publishTime": "2026-01-02T02:00:00Z",
                    "generation": 12,
                },
                {
                    "fuelType": "WIND",
                    "startTime": "2026-01-02T00:00:00Z",
                    "publishTime": "2026-01-02T01:00:00Z",
                    "generation": 10,
                },
            ]

        client.get_response.side_effect = lambda dataset, **kwargs: ProviderResponse(
            200, rows(dataset, **kwargs), {}
        )
        self.assertEqual(import_history(client), (1, 1))
        self.assertEqual(import_history(client), (1, 1))
        self.assertEqual(Actual.objects.count(), 1)
        self.assertEqual(Forecast.objects.count(), 1)
        self.assertEqual(Actual.objects.get().generation, 12)
        self.assertEqual(ImportRun.objects.count(), 2)


class APIContractTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_legacy_and_versioned_routes_are_equivalent(self):
        self.assertEqual(
            self.client.get("/api/dashboard/").json(),
            self.client.get("/api/v1/dashboard/").json(),
        )
        self.assertEqual(
            self.client.get("/api/status/").json(),
            self.client.get("/api/v1/status/").json(),
        )

    def test_csv_content_negotiation(self):
        for suffix in ["?export=csv", "?format=csv"]:
            response = self.client.get("/api/v1/dashboard/" + suffix)
            self.assertEqual(response.status_code, 200)
            self.assertIn("text/csv", response["Content-Type"])
            self.assertIn("attachment", response["Content-Disposition"])
            self.assertEqual(len(response.content.decode().splitlines()), 49)

    def test_invalid_parameters_have_field_errors(self):
        for query, field in [
            ("decision_date=2026-02-01", "decision_date"),
            ("cutoff=10:00Z", "cutoff"),
            ("export=pdf", "export"),
        ]:
            response = self.client.get("/api/v1/dashboard/?" + query)
            self.assertEqual(response.status_code, 400)
            self.assertIn(field, response.json()["errors"])

    def test_exact_cutoff_zero_actual_and_constant_query_count(self):
        Forecast.objects.create(
            start_time=datetime(2026, 1, 16, tzinfo=timezone.utc),
            publish_time=datetime(2026, 1, 15, 10, tzinfo=timezone.utc),
            generation=20,
        )
        Actual.objects.create(
            start_time=datetime(2026, 1, 16, tzinfo=timezone.utc), generation=0
        )
        with self.assertNumQueries(2):
            response = self.client.get("/api/v1/dashboard/")
        metrics = response.json()["data"]["metrics"]
        self.assertEqual(metrics["mae"], 20)
        self.assertIsNone(metrics["wape"])
