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
    core = core.copy()
    core["period"] = core["observation_date"].dt.to_period("M").dt.to_timestamp("M")
    monthly = (
        core.groupby(["age_band", "km_band", "period"], observed=True)
        .agg(
            median_price=("price", "median"),
            avg_price=("price", "mean"),
            listings_count=("price", "size"),
            avg_km=("km", "mean"),
            avg_age=("age", "mean"),
        )
        .reset_index()
    )
    monthly = add_cluster_id(monthly)
    monthly["week_number"] = monthly["period"].dt.isocalendar().week.astype(int)
    monthly["month"] = monthly["period"].dt.month
    monthly["riding_season_share"] = monthly["month"].between(4, 10).astype(float)
    return monthly.sort_values(["cluster_id", "period"]).reset_index(drop=True)
