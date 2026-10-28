"""Elexon HTTP client with Tenacity retries and pybreaker circuit protection."""

import requests
from common.circuit_breaker import get_circuit_breaker
from django.conf import settings
from tenacity import Retrying, retry_if_exception, stop_after_attempt, wait_exponential

from .utils import ProviderResponse


class ElexonClient:
    """Own API configuration, endpoint parameters and resilient HTTP requests."""

    ENDPOINTS = {
        "FUELHH": "FUELHH/stream",  # Actual generation; filter fuelType=WIND.
        "WINDFOR": "WINDFOR/stream",  # Forecast generation and publication time.
    }

    def __init__(self, *, base_url=None, timeout=None):
        self.base_url = (
            settings.ELEXON_BASE_URL if base_url is None else base_url
        ).rstrip("/")
        self.timeout = settings.ELEXON_TIMEOUT if timeout is None else timeout
        self.breaker = get_circuit_breaker(
            name=self.base_url,
            failure_threshold=settings.ELEXON_CIRCUIT_FAILURE_THRESHOLD,
            recovery_timeout=settings.ELEXON_CIRCUIT_RECOVERY_TIMEOUT,
            is_failure=self._is_upstream_failure,
        )
        self.retrying = Retrying(
            stop=stop_after_attempt(settings.ELEXON_RETRY_ATTEMPTS),
            wait=wait_exponential(multiplier=1, max=10),
            retry=retry_if_exception(self._is_upstream_failure),
            reraise=True,
        )

    @staticmethod
    def _is_upstream_failure(error):
        if isinstance(error, requests.HTTPError):
            response = error.response
            return (
                response is None
                or response.status_code == 429
                or response.status_code >= 500
            )
        return isinstance(error, (requests.RequestException, ValueError))

    def get_rows(self, dataset, params):
        """Convenience access to the raw dataset payload."""
        return self.get_response(dataset, params).payload

    def get_response(self, dataset, params):
        # Count a failed logical call only after Tenacity exhausts its attempts.
        return self.breaker.call(self._fetch_with_retry, dataset, params)

    def _fetch_with_retry(self, dataset, params):
        return self.retrying(self._fetch_rows, dataset, params)

    def _fetch_rows(self, dataset, params):
        response = requests.get(
            f"{self.base_url}/{self.ENDPOINTS[dataset]}",
            params=params,
            timeout=self.timeout,
        )
        return ProviderResponse.from_response(response, dataset)

    def get_wind_forecasts(self, published_from, published_to):
        """GET WINDFOR/stream, selecting forecast publication timestamps."""
        return self.get_response(
            "WINDFOR",
            params={
                "publishDateTimeFrom": published_from.isoformat(),
                "publishDateTimeTo": published_to.isoformat(),
            },
        )

    def get_wind_actuals(self, settlement_date):
        """GET FUELHH/stream for WIND actuals on the settlement date."""
        return self.get_response(
            "FUELHH",
            params={
                "settlementDateFrom": settlement_date.isoformat(),
                "settlementDateTo": settlement_date.isoformat(),
                "fuelType": "WIND",
            },
        )
