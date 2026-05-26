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
    return df[
        (df["market_segment"] == "modern")
        & (df["engine_cc"].between(CORE_MIN_CC, CORE_MAX_CC))
        & (df["price"].between(CORE_MIN_PRICE, CORE_MAX_PRICE))
    ].copy()


def add_age_km_bands(df):
    df = df.copy()
    df["age_band"] = pd.cut(df["age"], bins=AGE_BINS, labels=AGE_LABELS)
    df["km_band"] = pd.cut(df["km"], bins=KM_BINS, labels=KM_LABELS)
    return df


def add_cluster_id(df):
    df = df.copy()
    df["cluster_id"] = df["age_band"].astype(str) + "__" + df["km_band"].astype(str)
    return df
