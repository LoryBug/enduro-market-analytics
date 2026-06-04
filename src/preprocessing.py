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

SEASON_ORDER = {
    "winter": 1,
    "spring": 2,
    "summer": 3,
    "autumn": 4,
}


def load_raw_listings(path):
    """Load raw listings CSV and validate required columns.

    Args:
        path: Path to the raw CSV file.

    Returns:
        DataFrame with raw listings.

    Raises:
        ValueError: If any required column is missing.
    """
    df = pd.read_csv(path)
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    return df


def _to_numeric(series):
    """Convert a pandas Series to numeric, handling Italian-formatted numbers.

    Strips non-numeric characters, replaces comma with dot for decimal
    separator, and removes trailing ".0" strings.

    Args:
        series: Input Series (string, numeric, or mixed).

    Returns:
        Series with dtype float64.
    """
    if pd.api.types.is_numeric_dtype(series):
        return pd.to_numeric(series, errors="coerce")
    cleaned = series.astype(str).str.replace(r"[^0-9.,-]", "", regex=True)
    cleaned = cleaned.str.replace(r"\.0$", "", regex=True)
    cleaned = cleaned.str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
    return pd.to_numeric(cleaned, errors="coerce")


def clean_listings(df):
    """Clean raw listings: parse dates, cast types, engineer features.

    Steps: date parsing, numeric conversion, boolean coercion, filtering
    invalid rows, and feature creation (age, km_per_year, price_per_cc,
    segment flags, seasonal features).

    Args:
        df: Raw listings DataFrame.

    Returns:
        Cleaned and sorted DataFrame.
    """
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
    add_seasonal_features(df)

    return df.sort_values("observation_date").reset_index(drop=True)


def add_seasonal_features(df):
    """Add season and riding_season columns based on observation_date.

    Args:
        df: Listings DataFrame with 'observation_date' column.

    Returns:
        Same DataFrame with 'season' (winter/spring/summer/autumn) and
        'riding_season' (True for Apr-Oct) columns.
    """
    month = df["observation_date"].dt.month
    df["season"] = np.select(
        [month.isin([12, 1, 2]), month.isin([3, 4, 5]), month.isin([6, 7, 8])],
        ["winter", "spring", "summer"],
        default="autumn",
    )
    df["riding_season"] = month.between(4, 10)
    return df


def build_seasonal_market_summary(df):
    """Build seasonal comparison table (by season and by riding period).

    Args:
        df: Listings DataFrame with 'season' and 'riding_season' columns.

    Returns:
        DataFrame with listings count, median/avg/q prices, avg_km, avg_age
        grouped by season and riding_period.
    """
    season_summary = summarize_market_groups(df, "season", "season")
    season_summary["sort_order"] = season_summary["period_label"].map(SEASON_ORDER)

    riding_df = df.copy()
    riding_df["riding_period"] = np.where(riding_df["riding_season"], "riding_season_apr_oct", "off_season_nov_mar")
    riding_summary = summarize_market_groups(riding_df, "riding_period", "riding_period")
    riding_summary["sort_order"] = riding_summary["period_label"].map({"riding_season_apr_oct": 1, "off_season_nov_mar": 2})

    summary = pd.concat([season_summary, riding_summary], ignore_index=True)
    return summary.sort_values(["group_type", "sort_order"]).drop(columns="sort_order").reset_index(drop=True)


def summarize_market_groups(df, group_col, group_type):
    """Generic groupby summarizer for market segments.

    Args:
        df: Listings DataFrame.
        group_col: Column name to group by.
        group_type: Label for the group_type column.

    Returns:
        DataFrame with aggregated stats per group.
    """
    summary = (
        df.groupby(group_col)
        .agg(
            listings_count=("price", "size"),
            median_price=("price", "median"),
            avg_price=("price", "mean"),
            q25_price=("price", lambda value: value.quantile(0.25)),
            q75_price=("price", lambda value: value.quantile(0.75)),
            avg_km=("km", "mean"),
            avg_age=("age", "mean"),
        )
        .reset_index()
        .rename(columns={group_col: "period_label"})
    )
    summary.insert(0, "group_type", group_type)
    return summary


def build_weekly_market_series(df):
    """Aggregate listings to weekly market series.

    Args:
        df: Clean listings DataFrame.

    Returns:
        Weekly aggregated market series.
    """
    return build_market_series(df, frequency="W")


def build_monthly_market_series(df):
    """Aggregate listings to monthly market series.

    Args:
        df: Clean listings DataFrame.

    Returns:
        Monthly aggregated market series.
    """
    return build_market_series(df, frequency="M")


def build_market_series(df, frequency="W"):
    """Core resampling aggregation: time-indexed market indicators.

    Resamples listings by the given frequency and computes price metrics,
    composition shares, and temporal features. Only periods with at least
    one listing are kept.

    Args:
        df: Clean listings DataFrame.
        frequency: Pandas offset string ('W' or 'M').

    Returns:
        DataFrame with one row per period.

    Raises:
        ValueError: If df is empty.
    """
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
