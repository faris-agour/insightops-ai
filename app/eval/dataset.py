"""Golden dataset of (query -> expected intent) pairs.

Used by the eval harness to measure classification accuracy. Keep these realistic
and varied; add a case whenever a misclassification is found in production.
"""

from __future__ import annotations

GOLDEN_CASES: list[tuple[str, str]] = [
    # sales_report
    ("sales report", "sales_report"),
    ("generate a sales report", "sales_report"),
    ("give me an overview of sales", "sales_report"),
    ("summary of sales", "sales_report"),
    # sales_status
    ("how are sales doing", "sales_status"),
    ("current sales performance", "sales_status"),
    ("tell me about sales", "sales_status"),
    # top_product
    ("which product is selling the most", "top_product"),
    ("what is our best product", "top_product"),
    ("top performing item", "top_product"),
    # worst_product
    ("which product is the worst", "worst_product"),
    ("lowest selling product", "worst_product"),
    ("weakest product", "worst_product"),
    # sales_by_region
    ("compare sales by region", "sales_by_region"),
    ("which region performs best", "sales_by_region"),
    ("revenue by territory", "sales_by_region"),
    # anomaly_detection
    ("show me anomalies", "anomaly_detection"),
    ("are there any unusual spikes", "anomaly_detection"),
    ("detect outliers in revenue", "anomaly_detection"),
    # forecast_revenue
    ("forecast next week revenue", "forecast_revenue"),
    ("predict future sales", "forecast_revenue"),
    ("revenue projection", "forecast_revenue"),
    # trend_analysis
    ("what is the revenue trend", "trend_analysis"),
    ("show the growth trajectory", "trend_analysis"),
    # unknown
    ("check customer churn", "unknown"),
    ("what is the weather today", "unknown"),
]
