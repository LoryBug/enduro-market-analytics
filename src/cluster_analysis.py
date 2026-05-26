import numpy as np
import pandas as pd

from .config import AGE_LABELS, KM_LABELS, MIN_CLUSTER_COUNT
from .segments import add_cluster_id


def build_cluster_summary(core):
    grouped = (
        core.groupby(["age_band", "km_band"], observed=False)
        .agg(
            listings_count=("price", "size"),
            median_price=("price", "median"),
            avg_price=("price", "mean"),
            q25_price=("price", lambda value: value.quantile(0.25) if len(value) else np.nan),
            q75_price=("price", lambda value: value.quantile(0.75) if len(value) else np.nan),
            min_price=("price", "min"),
            max_price=("price", "max"),
            avg_age=("age", "mean"),
            avg_km=("km", "mean"),
        )
        .reset_index()
    )
    grouped["iqr_price"] = grouped["q75_price"] - grouped["q25_price"]
    grouped["coverage_status"] = np.select(
        [grouped["listings_count"] >= MIN_CLUSTER_COUNT, grouped["listings_count"] > 0],
        ["strong", "weak"],
        default="empty",
    )
    grouped["needs_more_observations"] = grouped["listings_count"].between(1, MIN_CLUSTER_COUNT - 1)
    grouped["rows_needed_to_min20"] = (MIN_CLUSTER_COUNT - grouped["listings_count"]).clip(lower=0)
    return grouped


def build_price_matrix(summary):
    return summary.pivot(index="age_band", columns="km_band", values="median_price").reindex(index=AGE_LABELS, columns=KM_LABELS)


def build_count_matrix(summary):
    return summary.pivot(index="age_band", columns="km_band", values="listings_count").reindex(index=AGE_LABELS, columns=KM_LABELS)


def build_monthly_cluster_series(core):
    monthly = (
        core.set_index("observation_date")
        .groupby(["age_band", "km_band"], observed=True)
        .resample("M")
        .agg(
            median_price=("price", "median"),
            avg_price=("price", "mean"),
            listings_count=("price", "size"),
            avg_km=("km", "mean"),
            avg_age=("age", "mean"),
        )
        .reset_index()
        .rename(columns={"observation_date": "period"})
    )
    monthly = add_cluster_id(monthly)
    monthly["week_number"] = monthly["period"].dt.isocalendar().week.astype(int)
    monthly["month"] = monthly["period"].dt.month
    for col in ["median_price", "avg_price", "avg_km", "avg_age"]:
        monthly[col] = monthly.groupby("cluster_id", observed=True)[col].transform(lambda value: value.interpolate(limit_direction="both"))
    monthly["listings_count"] = monthly["listings_count"].fillna(0).astype(int)
    return monthly
