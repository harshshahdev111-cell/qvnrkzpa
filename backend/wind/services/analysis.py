from datetime import datetime, time, timedelta
from math import sqrt

from wind.constants import PERIOD_MINUTES, PERIODS_PER_DAY, UTC
from wind.selectors import actuals_for_delivery, eligible_forecasts


def analyze(day, cutoff):
    decision = datetime.combine(day, cutoff, tzinfo=UTC)
    start = datetime.combine(day + timedelta(days=1), time(), tzinfo=UTC)
    end = start + timedelta(days=1)
    forecasts = {}
    for f in eligible_forecasts(start, end, decision):
        forecasts[f.start_time] = f
    actuals = {a.start_time: a.generation for a in actuals_for_delivery(start, end)}
    rows = []
    for i in range(PERIODS_PER_DAY):
        target = start + timedelta(minutes=i * PERIOD_MINUTES)
        f = forecasts.get(target)
        a = actuals.get(target)
        rows.append(
            {
                "start_time": target,
                "forecast": f.generation if f else None,
                "actual": a,
                "publish_time": f.publish_time if f else None,
                "error": f.generation - a if f and a is not None else None,
            }
        )
    paired = [r for r in rows if r["error"] is not None]
    errors = [r["error"] for r in paired]
    n = len(errors)
    total = sum(abs(r["actual"]) for r in paired)
    return {
        "decision_time": decision,
        "delivery_date": start.date(),
        "rows": rows,
        "metrics": {
            "mae": sum(map(abs, errors)) / n if n else None,
            "rmse": sqrt(sum(e * e for e in errors) / n) if n else None,
            "bias": sum(errors) / n if n else None,
            "wape": 100 * sum(map(abs, errors)) / total if total else None,
            "matched_periods": n,
            "forecast_periods": len(forecasts),
            "actual_periods": len(actuals),
            "expected_periods": PERIODS_PER_DAY,
            "forecast_energy_mwh": (
                sum(f.generation * 0.5 for f in forecasts.values())
                if forecasts
                else None
            ),
        },
    }
