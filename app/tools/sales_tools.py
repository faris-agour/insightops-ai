from pathlib import Path

import pandas as pd


DATA_FILE = Path(__file__).resolve().parents[2] / "data" / "sales.csv"


def analyze_sales() -> dict[str, float | str]:
    sales_df = pd.read_csv(DATA_FILE)

    required_columns = {"date", "product", "revenue"}
    missing_columns = required_columns.difference(sales_df.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"sales.csv is missing required columns: {missing}")

    sales_df["revenue"] = pd.to_numeric(sales_df["revenue"], errors="coerce").fillna(0)
    total_revenue = float(sales_df["revenue"].sum())

    daily_revenue = sales_df.groupby("date", as_index=False)["revenue"].sum()
    average_daily_revenue = float(daily_revenue["revenue"].mean()) if not daily_revenue.empty else 0.0

    product_revenue = sales_df.groupby("product", as_index=False)["revenue"].sum()
    top_product = ""
    worst_product = ""
    if not product_revenue.empty:
        top_product = str(product_revenue.loc[product_revenue["revenue"].idxmax(), "product"])
        worst_product = str(product_revenue.loc[product_revenue["revenue"].idxmin(), "product"])

    return {
        "total_revenue": round(total_revenue, 2),
        "average_daily_revenue": round(average_daily_revenue, 2),
        "top_product": top_product,
        "worst_product": worst_product,
    }
