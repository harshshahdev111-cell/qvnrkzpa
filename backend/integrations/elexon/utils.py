"""Small, reusable validators for Elexon response data."""

import math
from dataclasses import dataclass
from datetime import timezone

from django.utils.dateparse import parse_datetime


@dataclass(frozen=True)
class ProviderResponse:
    """Decoded provider response, retaining HTTP metadata for service callers."""

    status_code: int
    payload: list[dict]
    headers: dict

    @classmethod
    def from_response(cls, response, dataset):
        response.raise_for_status()
        return cls(
            status_code=response.status_code,
            payload=validate_rows(response.json(), dataset),
            headers=dict(response.headers),
        )


def validate_rows(value, dataset):
    """Require a dataset array of JSON objects before parsing individual rows."""
    if not isinstance(value, list):
        raise ValueError(f"Expected {dataset} array")
    if any(not isinstance(row, dict) for row in value):
        raise ValueError(f"Expected {dataset} rows to be objects")
    return value


def timestamp(value):
    """Parse an ISO timestamp, treating an omitted offset as UTC."""
    if not isinstance(value, str):
        raise ValueError(f"Invalid timestamp: {value}")
    try:
        parsed = parse_datetime(value)
    except ValueError as exc:
        raise ValueError(f"Invalid timestamp: {value}") from exc
    if parsed is None:
        raise ValueError(f"Invalid timestamp: {value}")
    return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed


def generation(value, kind):
    """Require a finite, nonnegative generation measurement, including zero."""
    try:
        if isinstance(value, bool):
            raise ValueError
        parsed = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"Invalid {kind} generation") from exc
    if not math.isfinite(parsed) or parsed < 0:
        raise ValueError(f"Invalid {kind} generation")
    return parsed
