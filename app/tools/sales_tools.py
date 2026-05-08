from pathlib import Path

import pandas as pd


DATA_FILE = Path(__file__).resolve().parents[2] / "data" / "sales.csv"


def _load_sales_data() -> pd.DataFrame:
    sales_df = pd.read_csv(DATA_FILE)

    required_columns = {"date", "product", "region", "revenue"}
    missing_columns = required_columns.difference(sales_df.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"sales.csv is missing required columns: {missing}")

    sales_df["date"] = pd.to_datetime(sales_df["date"], errors="coerce")
    sales_df["revenue"] = pd.to_numeric(sales_df["revenue"], errors="coerce").fillna(0)
    sales_df = sales_df.dropna(subset=["date"])
    return sales_df


def _daily_revenue(sales_df: pd.DataFrame) -> pd.DataFrame:
    daily_revenue_df = sales_df.copy()
    daily_revenue_df["date_only"] = daily_revenue_df["date"].dt.date
    return daily_revenue_df.groupby("date_only", as_index=False)["revenue"].sum()


def _product_revenue(sales_df: pd.DataFrame) -> pd.DataFrame:
    return sales_df.groupby("product", as_index=False)["revenue"].sum()


def get_sales_summary() -> dict[str, float | str]:
    sales_df = _load_sales_data()
    total_revenue = float(sales_df["revenue"].sum())

    daily_revenue = _daily_revenue(sales_df)
    average_daily_revenue = float(daily_revenue["revenue"].mean()) if not daily_revenue.empty else 0.0

    product_revenue = _product_revenue(sales_df)
    if product_revenue.empty:
        return {
            "total_revenue": round(total_revenue, 2),
            "average_daily_revenue": round(average_daily_revenue, 2),
            "top_product": "",
            "worst_product": "",
        }

    top_row = product_revenue.loc[product_revenue["revenue"].idxmax()]
    worst_row = product_revenue.loc[product_revenue["revenue"].idxmin()]

    return {
        "total_revenue": round(total_revenue, 2),
        "average_daily_revenue": round(average_daily_revenue, 2),
        "top_product": str(top_row["product"]),
        "worst_product": str(worst_row["product"]),
    }


def get_sales_status() -> dict[str, float | str]:
    sales_df = _load_sales_data()
    daily_revenue = _daily_revenue(sales_df)
    total_revenue = float(sales_df["revenue"].sum())
    average_daily_revenue = float(daily_revenue["revenue"].mean()) if not daily_revenue.empty else 0.0

    if daily_revenue.empty:
        return {
            "total_revenue": 0.0,
            "average_daily_revenue": 0.0,
            "trend": "no_data",
            "daily_variation_pct": 0.0,
            "daily_change_percent": 0.0,
        }

    first_day_revenue = float(daily_revenue.iloc[0]["revenue"])
    last_day_revenue = float(daily_revenue.iloc[-1]["revenue"])
    
    daily_change_percent = 0.0
    if first_day_revenue > 0:
        daily_change_percent = ((last_day_revenue - first_day_revenue) / first_day_revenue) * 100
    
    if first_day_revenue == 0:
        trend = "stable"
    elif last_day_revenue > first_day_revenue * 1.05:
        trend = "increasing"
    elif last_day_revenue < first_day_revenue * 0.95:
        trend = "decreasing"
    else:
        trend = "stable"

    variation = daily_revenue["revenue"].pct_change().abs().fillna(0)
    daily_variation_pct = float(variation.mean() * 100)

    return {
        "total_revenue": round(total_revenue, 2),
        "average_daily_revenue": round(average_daily_revenue, 2),
        "trend": trend,
        "daily_variation_pct": round(daily_variation_pct, 2),
        "daily_change_percent": round(daily_change_percent, 2),
    }


def get_top_product() -> dict[str, float | str]:
    sales_df = _load_sales_data()
    product_revenue = _product_revenue(sales_df)
    if product_revenue.empty:
        return {"product": "", "revenue": 0.0, "percent_of_total_revenue": 0.0}

    total_revenue = float(product_revenue["revenue"].sum())
    top_row = product_revenue.loc[product_revenue["revenue"].idxmax()]
    top_revenue = float(top_row["revenue"])
    pct = (top_revenue / total_revenue * 100) if total_revenue > 0 else 0.0
    
    return {
        "product": str(top_row["product"]),
        "revenue": round(top_revenue, 2),
        "percent_of_total_revenue": round(pct, 1),
    }


def get_worst_product() -> dict[str, float | str]:
    sales_df = _load_sales_data()
    product_revenue = _product_revenue(sales_df)
    if product_revenue.empty:
        return {"product": "", "revenue": 0.0, "percent_of_total_revenue": 0.0}

    total_revenue = float(product_revenue["revenue"].sum())
    worst_row = product_revenue.loc[product_revenue["revenue"].idxmin()]
    worst_revenue = float(worst_row["revenue"])
    pct = (worst_revenue / total_revenue * 100) if total_revenue > 0 else 0.0
    
    return {
        "product": str(worst_row["product"]),
        "revenue": round(worst_revenue, 2),
        "percent_of_total_revenue": round(pct, 1),
    }


def get_sales_by_region() -> dict[str, object]:
    sales_df = _load_sales_data()
    region_revenue = (
        sales_df.groupby("region", as_index=False)["revenue"]
        .sum()
        .sort_values("revenue", ascending=False)
        .reset_index(drop=True)
    )

    if region_revenue.empty:
        return {
            "best_region": "",
            "best_region_revenue": 0.0,
            "worst_region": "",
            "worst_region_revenue": 0.0,
            "regions": [],
        }

    best_row = region_revenue.iloc[0]
    worst_row = region_revenue.iloc[-1]

    regions = [
        {
            "region": str(row["region"]),
            "revenue": round(float(row["revenue"]), 2),
        }
        for _, row in region_revenue.iterrows()
    ]

    return {
        "best_region": str(best_row["region"]),
        "best_region_revenue": round(float(best_row["revenue"]), 2),
        "worst_region": str(worst_row["region"]),
        "worst_region_revenue": round(float(worst_row["revenue"]), 2),
        "regions": regions,
    }


def analyze_sales() -> dict[str, float | str]:
    return get_sales_summary()
