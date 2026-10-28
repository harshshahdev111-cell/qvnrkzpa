"""Time boundaries for the January 2026 decision pilot."""

from datetime import datetime, timezone

UTC = timezone.utc
FIRST = datetime(2026, 1, 1, tzinfo=UTC)
END = datetime(2026, 2, 1, tzinfo=UTC)
PERIODS_PER_DAY = 48
PERIOD_MINUTES = 30
