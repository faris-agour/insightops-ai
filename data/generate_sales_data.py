from pathlib import Path

import numpy as np
import pandas as pd


OUTPUT_FILE = Path(__file__).resolve().parent / "sales.csv"


def generate_sales_data(output_file: Path = OUTPUT_FILE, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    products = [
        "Monitoring Suite",
        "Analytics Pack",
        "Reporting Add-on",
        "Insight Assistant",
    ]
    regions = ["North", "South", "East"]
    channels = ["Online", "Partner", "Direct"]

    product_base_units = {
        "Monitoring Suite": 26,
        "Analytics Pack": 21,
        "Reporting Add-on": 14,
        "Insight Assistant": 17,
    }
    product_price = {
        "Monitoring Suite": 125.0,
        "Analytics Pack": 155.0,
        "Reporting Add-on": 95.0,
        "Insight Assistant": 180.0,
    }
    product_cost = {
        "Monitoring Suite": 66.0,
        "Analytics Pack": 79.0,
        "Reporting Add-on": 52.0,
        "Insight Assistant": 102.0,
    }

    region_factor = {"North": 1.05, "South": 0.95, "East": 1.1}
    channel_factor = {"Online": 1.0, "Partner": 1.15, "Direct": 0.9}

    days = 21
    start_date = pd.Timestamp("2026-01-01")
    inconsistent_days = {4: 0.62, 9: 1.34, 15: 0.71}

    records: list[dict[str, object]] = []

    for day_idx in range(days):
        current_date = start_date + pd.Timedelta(days=day_idx)
        weekend_factor = 0.88 if current_date.dayofweek >= 5 else 1.0
        day_factor = inconsistent_days.get(day_idx, 1.0)

        for product in products:
            for region in regions:
                channel = str(rng.choice(channels, p=[0.45, 0.35, 0.2]))

                units = product_base_units[product]
                units *= region_factor[region] * channel_factor[channel] * weekend_factor * day_factor
                units *= float(rng.normal(1.0, 0.08))
                units_sold = max(3, int(round(units)))

                if region == "South" and day_idx in {10, 11, 12}:
                    units_sold = max(2, int(round(units_sold * 0.28)))

                if product == "Analytics Pack" and day_idx == 16:
                    units_sold = int(round(units_sold * 2.9))

                unit_price = product_price[product] * float(rng.normal(1.0, 0.03))
                revenue = round(units_sold * unit_price, 2)

                unit_cost = product_cost[product] * float(rng.normal(1.0, 0.025))
                cost = round(units_sold * unit_cost, 2)

                records.append(
                    {
                        "date": current_date.strftime("%Y-%m-%d"),
                        "product": product,
                        "region": region,
                        "channel": channel,
                        "units_sold": units_sold,
                        "revenue": revenue,
                        "cost": cost,
                    }
                )

    sales_df = pd.DataFrame(records)
    sales_df = sales_df.sort_values(["date", "region", "product"]).reset_index(drop=True)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    sales_df.to_csv(output_file, index=False)

    return sales_df


if __name__ == "__main__":
    dataset = generate_sales_data()
    print(f"Generated {len(dataset)} rows in {OUTPUT_FILE}")
