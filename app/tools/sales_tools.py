from pathlib import Path

import pandas as pd


DATA_FILE = Path(__file__).resolve().parents[2] / "data" / "sales.csv"


def analyze_sales() -> dict[str, float]:
    sales_df = pd.read_csv(DATA_FILE)

    if "revenue" not in sales_df.columns:
        raise ValueError("sales.csv must include a 'revenue' column")

    revenue_series = pd.to_numeric(sales_df["revenue"], errors="coerce").fillna(0)
    total_revenue = float(revenue_series.sum())

    return {"total_revenue": total_revenue}
