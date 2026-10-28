"""Fetch, normalize and atomically upsert historical source data."""

from datetime import timedelta

import requests
from django.db import transaction
from integrations.elexon import ElexonService
from pybreaker import CircuitBreakerError

from wind.constants import END, FIRST
from wind.models import Actual, Forecast, ImportRun


class ImportFailure(Exception):
    """An upstream or validation failure; no partial import is committed."""


def import_history(client, report=lambda message: None):
    service = ElexonService(client)
    actuals = {}
    forecasts = {}
    try:
        # Seven-day lookback captures older forecast vintages available on January 1.
        day = FIRST - timedelta(days=7)
        while day < END:
            following = day + timedelta(days=1)
            records = service.get_wind_forecasts(day, following)
            for row in records:
                start = row["start_time"]
                published = row["publish_time"]
                if (
                    FIRST + timedelta(days=1) <= start < END + timedelta(days=1)
                    and published < END
                ):
                    forecasts[start, published] = Forecast(
                        start_time=start,
                        publish_time=published,
                        generation=row["generation"],
                    )
            report(f"Forecast publications {day.date()}: {len(records)} rows")
            day = following
        day = FIRST + timedelta(days=1)
        while day < END + timedelta(days=1):
            records = service.get_wind_actuals(day.date())
            for row in records:
                start = row["start_time"]
                published = row["publish_time"]
                if FIRST + timedelta(days=1) <= start < END + timedelta(days=1):
                    old = actuals.get(start)
                    if old is None or (
                        published
                        and (old.publish_time is None or published > old.publish_time)
                    ):
                        actuals[start] = Actual(
                            start_time=start,
                            publish_time=published,
                            generation=row["generation"],
                        )
            report(f"Actuals {day.date()}: {len(records)} rows")
            day += timedelta(days=1)
        if not actuals or not forecasts:
            raise ValueError("Empty dataset; previous import retained")
        with transaction.atomic():
            Actual.objects.bulk_create(
                actuals.values(),
                update_conflicts=True,
                unique_fields=["start_time"],
                update_fields=["generation", "publish_time"],
            )
            Forecast.objects.bulk_create(
                forecasts.values(),
                update_conflicts=True,
                unique_fields=["start_time", "publish_time"],
                update_fields=["generation"],
            )
            ImportRun.objects.create(actuals=len(actuals), forecasts=len(forecasts))
    except (
        CircuitBreakerError,
        requests.RequestException,
        ValueError,
        KeyError,
        TypeError,
    ) as exc:
        raise ImportFailure(f"Import failed; no partial data committed: {exc}") from exc
    return len(actuals), len(forecasts)
