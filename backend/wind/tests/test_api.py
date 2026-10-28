from datetime import datetime, timezone

from django.test import TestCase
from rest_framework.test import APIClient

from wind.models import Actual, Forecast


class AnalysisTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.t = datetime(2026, 1, 16, tzinfo=timezone.utc)
        Actual.objects.create(start_time=self.t, generation=100)
        for hour, value in [(8, 120), (9, 110), (11, 500)]:
            Forecast.objects.create(
                start_time=self.t,
                publish_time=datetime(2026, 1, 15, hour, tzinfo=timezone.utc),
                generation=value,
            )

    def test_cutoff_prevents_lookahead_and_metrics(self):
        r = self.client.get(
            "/api/dashboard/?decision_date=2026-01-15&cutoff=10:00"
        ).json()["data"]
        self.assertEqual(r["rows"][0]["forecast"], 110)
        self.assertEqual(r["metrics"]["mae"], 10)
        self.assertEqual(r["metrics"]["rmse"], 10)
        self.assertEqual(r["metrics"]["bias"], 10)
        self.assertEqual(r["metrics"]["wape"], 10)
        self.assertEqual(r["metrics"]["matched_periods"], 1)
        self.assertIsNone(r["rows"][1]["forecast"])

    def test_empty_and_invalid(self):
        self.assertIsNone(
            self.client.get("/api/dashboard/?decision_date=2026-01-01").json()["data"][
                "metrics"
            ]["mae"]
        )
        self.assertEqual(
            self.client.get("/api/dashboard/?decision_date=2026-02-01").status_code, 400
        )
        self.assertEqual(
            self.client.get("/api/dashboard/?cutoff=invalid").status_code, 400
        )

    def test_last_decision_delivers_february(self):
        r = self.client.get("/api/dashboard/?decision_date=2026-01-31").json()["data"]
        self.assertEqual(r["delivery_date"], "2026-02-01")

    def test_csv(self):
        r = self.client.get("/api/dashboard/?export=csv")
        self.assertEqual(r.status_code, 200)
        self.assertIn(
            "start_time,forecast,actual,publish_time,error", r.content.decode()
        )
