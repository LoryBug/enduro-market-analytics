import pandas as pd

from .config import (
    AGE_BINS,
    AGE_LABELS,
    CORE_MAX_CC,
    CORE_MAX_PRICE,
    CORE_MIN_CC,
    CORE_MIN_PRICE,
    KM_BINS,
    KM_LABELS,
)


def filter_core_market(df):
    """Filter listings to core modern enduro segment.

    Core criteria: modern market segment, 250-500cc engine, 1000-20000€ price.

    Args:
        df: Listings DataFrame with market_segment, engine_cc, price columns.

    Returns:
        Filtered DataFrame with only core market listings.
    """
    return df[
        (df["market_segment"] == "modern")
        & (df["engine_cc"].between(CORE_MIN_CC, CORE_MAX_CC))
        & (df["price"].between(CORE_MIN_PRICE, CORE_MAX_PRICE))
    ].copy()


def add_age_km_bands(df):
    """Assign age and kilometrage band labels to each listing.

    Bands are defined in config: age (0-2, 3-5, 6-10, 11-20, 20+) and
    km (0-5k, 5-10k, 10-15k, 15k+).

    Args:
        df: Listings DataFrame with 'age' and 'km' columns.

    Returns:
        DataFrame with 'age_band' and 'km_band' columns.
    """
    df = df.copy()
    df["age_band"] = pd.cut(df["age"], bins=AGE_BINS, labels=AGE_LABELS)
    df["km_band"] = pd.cut(df["km"], bins=KM_BINS, labels=KM_LABELS)
    return df


def add_cluster_id(df):
    """Create composite cluster ID from age_band and km_band.

    Format: "{age_band}__{km_band}" e.g. "3-5__0-5k".

    Args:
        df: DataFrame with 'age_band' and 'km_band' columns.

    Returns:
        DataFrame with 'cluster_id' column.
    """
    df = df.copy()
    df["cluster_id"] = df["age_band"].astype(str) + "__" + df["km_band"].astype(str)
    return df
