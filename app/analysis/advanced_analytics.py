from typing import Any

import pandas as pd

from app.tools.sales_tools import _daily_revenue, load_sales_data


def detect_anomalies(z_threshold: float = 2.0) -> dict[str, Any]:
    sales_df = load_sales_data()
    daily = _daily_revenue(sales_df)

    if daily.empty or len(daily) < 3:
        return {
            "anomalies": [],
            "method": "z_score",
            "threshold": z_threshold,
            "total_days_analyzed": len(daily),
        }

    revenues = daily["revenue"].astype(float)
    mean = float(revenues.mean())
    std = float(revenues.std()) or 1e-9

    daily = daily.copy()
    daily["z_score"] = (revenues - mean) / std
    anomaly_rows = daily[daily["z_score"].abs() >= z_threshold]

    anomalies = [
        {
            "date": str(row["date_only"]),
            "revenue": round(float(row["revenue"]), 2),
            "z_score": round(float(row["z_score"]), 2),
            "direction": "spike" if row["z_score"] > 0 else "drop",
        }
        for _, row in anomaly_rows.iterrows()
    ]

    return {
        "anomalies": anomalies,
        "method": "z_score",
        "threshold": z_threshold,
        "mean_daily_revenue": round(mean, 2),
        "std_daily_revenue": round(std, 2),
        "total_days_analyzed": len(daily),
        "anomaly_count": len(anomalies),
    }


def forecast_revenue(horizon_days: int = 7) -> dict[str, Any]:
    sales_df = load_sales_data()
    daily = _daily_revenue(sales_df)

    if daily.empty or len(daily) < 2:
        return {
            "forecast": [],
            "method": "linear_regression",
            "horizon_days": horizon_days,
            "history_days": len(daily),
        }

    daily = daily.copy().sort_values("date_only").reset_index(drop=True)
    daily["day_index"] = range(len(daily))

    x = daily["day_index"].astype(float)
    y = daily["revenue"].astype(float)
    n = len(x)
    x_mean = float(x.mean())
    y_mean = float(y.mean())
    denominator = float(((x - x_mean) ** 2).sum()) or 1e-9
    slope = float(((x - x_mean) * (y - y_mean)).sum()) / denominator
    intercept = y_mean - slope * x_mean

    last_date = pd.to_datetime(daily["date_only"].iloc[-1])
    last_index = int(daily["day_index"].iloc[-1])

    forecast = []
    for step in range(1, horizon_days + 1):
        future_index = last_index + step
        predicted = max(0.0, intercept + slope * future_index)
        future_date = (last_date + pd.Timedelta(days=step)).date()
        forecast.append(
            {
                "date": str(future_date),
                "predicted_revenue": round(predicted, 2),
            }
        )

    direction = "increasing" if slope > 0 else "decreasing" if slope < 0 else "flat"

    return {
        "forecast": forecast,
        "method": "linear_regression",
        "horizon_days": horizon_days,
        "history_days": n,
        "trend_direction": direction,
        "daily_growth_estimate": round(slope, 2),
        "baseline_average": round(y_mean, 2),
    }


def analyze_trend(window: int = 7) -> dict[str, Any]:
    sales_df = load_sales_data()
    daily = _daily_revenue(sales_df).sort_values("date_only").reset_index(drop=True)

    if daily.empty:
        return {
            "moving_average": [],
            "window": window,
            "trend": "no_data",
            "history_days": 0,
        }

    actual_window = min(window, len(daily))
    rolling = daily["revenue"].astype(float).rolling(window=actual_window, min_periods=1).mean()

    series = [
        {
            "date": str(row["date_only"]),
            "revenue": round(float(row["revenue"]), 2),
            "moving_average": round(float(rolling.iloc[idx]), 2),
        }
        for idx, (_, row) in enumerate(daily.iterrows())
    ]

    if len(rolling) >= 2:
        first_avg = float(rolling.iloc[0])
        last_avg = float(rolling.iloc[-1])
        change_pct = ((last_avg - first_avg) / first_avg * 100) if first_avg > 0 else 0.0
        if change_pct > 5:
            trend = "increasing"
        elif change_pct < -5:
            trend = "decreasing"
        else:
            trend = "stable"
    else:
        change_pct = 0.0
        trend = "stable"

    return {
        "moving_average": series,
        "window": actual_window,
        "trend": trend,
        "change_percent": round(change_pct, 2),
        "history_days": len(daily),
    }
