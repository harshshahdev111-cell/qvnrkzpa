"""Explicit contracts for API inputs and JSON responses."""

from datetime import date, time

from rest_framework import serializers


class DecisionQuerySerializer(serializers.Serializer):
    decision_date = serializers.DateField(default=date(2026, 1, 15))
    cutoff = serializers.TimeField(
        default=time(10), input_formats=["%H:%M", "%H:%M:%S"]
    )
    export = serializers.ChoiceField(choices=["csv"], required=False)

    def validate_decision_date(self, value):
        if value.year != 2026 or value.month != 1:
            raise serializers.ValidationError("Choose a decision date in January 2026.")
        return value


class PeriodSerializer(serializers.Serializer):
    start_time = serializers.DateTimeField()
    forecast = serializers.FloatField(allow_null=True)
    actual = serializers.FloatField(allow_null=True)
    publish_time = serializers.DateTimeField(allow_null=True)
    error = serializers.FloatField(allow_null=True)


class MetricsSerializer(serializers.Serializer):
    mae = serializers.FloatField(allow_null=True)
    rmse = serializers.FloatField(allow_null=True)
    bias = serializers.FloatField(allow_null=True)
    wape = serializers.FloatField(allow_null=True)
    matched_periods = serializers.IntegerField()
    forecast_periods = serializers.IntegerField()
    actual_periods = serializers.IntegerField()
    expected_periods = serializers.IntegerField()
    forecast_energy_mwh = serializers.FloatField(allow_null=True)


class DashboardSerializer(serializers.Serializer):
    decision_time = serializers.DateTimeField()
    delivery_date = serializers.DateField()
    rows = PeriodSerializer(many=True)
    metrics = MetricsSerializer()


class SourceStatusSerializer(serializers.Serializer):
    source = serializers.CharField()
    actuals = serializers.IntegerField()
    forecasts = serializers.IntegerField()
    last_import = serializers.DateTimeField(allow_null=True)
    synthetic = serializers.BooleanField()
