import numpy as np
import pandas as pd

from .config import CURRENT_YEAR


REQUIRED_COLUMNS = [
    "listing_date",
    "source",
    "brand",
    "model",
    "year",
    "km",
    "engine_cc",
    "price",
    "region",
    "province",
    "seller_type",
    "is_2stroke",
    "condition_score",
    "has_documents",
]


def load_raw_listings(path):
    df = pd.read_csv(path)
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    return df


def _to_numeric(series):
    if pd.api.types.is_numeric_dtype(series):
        return pd.to_numeric(series, errors="coerce")
    cleaned = series.astype(str).str.replace(r"[^0-9.,-]", "", regex=True)
    cleaned = cleaned.str.replace(r"\.0$", "", regex=True)
    cleaned = cleaned.str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
    return pd.to_numeric(cleaned, errors="coerce")


def clean_listings(df):
    df = df.copy()
    df["listing_date"] = pd.to_datetime(df["listing_date"], errors="coerce")
    if "snapshot_date" in df.columns:
        df["snapshot_date"] = pd.to_datetime(df["snapshot_date"], errors="coerce")

    for col in ["year", "km", "engine_cc", "price", "condition_score"]:
        df[col] = _to_numeric(df[col])

    for col in ["brand", "model", "source", "region", "province", "seller_type"]:
        df[col] = df[col].astype(str).str.strip().str.lower()

    for col in ["is_2stroke", "has_documents"]:
        df[col] = df[col].astype(str).str.strip().str.lower().isin(["1", "true", "yes", "y", "si", "sì"])

    df = df.dropna(subset=["listing_date", "year", "price"])
    df = df[(df["price"] > 0) & (df["year"] >= 1960) & (df["year"] <= CURRENT_YEAR)]

    df["age"] = (CURRENT_YEAR - df["year"]).clip(lower=0)
    df["km_per_year"] = df["km"] / df["age"].replace(0, 1)
    df["price_per_cc"] = df["price"] / df["engine_cc"].replace(0, np.nan)
    df["is_vintage"] = df["year"] < 1995
    df["is_youngtimer"] = (df["year"] >= 1995) & (df["year"] < 2010)
    df["market_segment"] = np.select(
        [df["is_vintage"], df["is_youngtimer"]],
        ["vintage", "youngtimer"],
        default="modern",
    )

    df["observation_date"] = df["listing_date"]

    return df.sort_values("observation_date").reset_index(drop=True)


def build_weekly_market_series(df):
    return build_market_series(df, frequency="W")


def build_monthly_market_series(df):
    return build_market_series(df, frequency="M")


def build_market_series(df, frequency="W"):
    if df.empty:
        raise ValueError("Cannot build market series from an empty listings dataset")

    series = (
        df.set_index("observation_date")
        .resample(frequency)
        .agg(
            avg_price=("price", "mean"),
            median_price=("price", "median"),
            listings_count=("price", "count"),
            avg_km=("km", "mean"),
            avg_age=("age", "mean"),
            vintage_share=("is_vintage", "mean"),
            youngtimer_share=("is_youngtimer", "mean"),
            two_stroke_share=("is_2stroke", "mean"),
        )
        .reset_index()
        .rename(columns={"observation_date": "period"})
    )

    series = series[series["listings_count"] > 0].copy()
    series["week_number"] = series["period"].dt.isocalendar().week.astype(int)
    series["month"] = series["period"].dt.month

    return series
