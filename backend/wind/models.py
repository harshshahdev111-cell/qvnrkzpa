from django.db import models


class Actual(models.Model):
    start_time = models.DateTimeField(unique=True)
    generation = models.FloatField()
    publish_time = models.DateTimeField(null=True)


class Forecast(models.Model):
    start_time = models.DateTimeField(db_index=True)
    publish_time = models.DateTimeField(db_index=True)
    generation = models.FloatField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["start_time", "publish_time"], name="unique_forecast_vintage"
            )
        ]


class ImportRun(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    actuals = models.PositiveIntegerField()
    forecasts = models.PositiveIntegerField()
