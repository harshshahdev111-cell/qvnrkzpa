"""Application-facing access to parsed Elexon data; no database operations."""

from .client import ElexonClient
from .utils import generation, timestamp, validate_rows


class ElexonService:
    """Fetch through a provider client and normalize upstream field names."""

    def __init__(self, client=None):
        self.client = client if client is not None else ElexonClient()

    def get_wind_forecasts(self, published_from, published_to):
        response = self.client.get_wind_forecasts(published_from, published_to)
        return self.parse_wind_forecasts(response.payload)

    def get_wind_actuals(self, settlement_date):
        response = self.client.get_wind_actuals(settlement_date)
        return self.parse_wind_actuals(response.payload)

    @staticmethod
    def parse_wind_forecasts(rows):
        """Normalize forecast vintages without applying application date windows."""
        return [
            {
                "start_time": timestamp(row["startTime"]),
                "publish_time": timestamp(row["publishTime"]),
                "generation": generation(row["generation"], "forecast"),
            }
            for row in validate_rows(rows, "WINDFOR")
        ]

    @staticmethod
    def parse_wind_actuals(rows):
        """Normalize wind actuals; upstream publication times may be absent."""
        return [
            {
                "start_time": timestamp(row["startTime"]),
                "publish_time": (
                    timestamp(row["publishTime"]) if row.get("publishTime") else None
                ),
                "generation": generation(row["generation"], "actual"),
            }
            for row in validate_rows(rows, "FUELHH")
            if row.get("fuelType") == "WIND"
        ]
