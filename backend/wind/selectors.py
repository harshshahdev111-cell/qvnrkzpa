"""Read-only database queries shared by application services."""

from django.db.models import OuterRef, Subquery

from .models import Actual, Forecast, ImportRun


def eligible_forecasts(start, end, decision):
    """Select one latest eligible vintage per target in the database."""
    latest = (
        Forecast.objects.filter(
            start_time=OuterRef("start_time"), publish_time__lte=decision
        )
        .order_by("-publish_time")
        .values("pk")[:1]
    )
    return Forecast.objects.filter(
        start_time__gte=start, start_time__lt=end, pk=Subquery(latest)
    ).order_by("start_time")


def actuals_for_delivery(start, end):
    return Actual.objects.filter(start_time__gte=start, start_time__lt=end)


def source_status():
    run = ImportRun.objects.order_by("-created_at").first()
    return {
        "source": "Elexon BMRS · FUELHH WIND / WINDFOR",
        "actuals": Actual.objects.count(),
        "forecasts": Forecast.objects.count(),
        "last_import": run.created_at if run else None,
        "synthetic": False,
    }
