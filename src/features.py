import pandas as pd


def make_lagged_features(series_df, target, lag_count=4):
    """Create lagged target, rolling features, and static features.

    Transforms a time series into a supervised learning dataset by adding
    lag columns, rolling statistics, and composition features. Automatically
    includes riding_season_share if present.

    Args:
        series_df: Time series DataFrame with 'period' and target column.
        target: Name of the target column.
        lag_count: Number of lag features to create.

    Returns:
        Tuple of (feature_df, feature_cols_list).
    """
    df = series_df.copy().sort_values("period")
    for lag in range(1, lag_count + 1):
        df[f"{target}_lag_{lag}"] = df[target].shift(lag)

    df["rolling_mean_4"] = df[target].shift(1).rolling(4).mean()
    df["rolling_std_4"] = df[target].shift(1).rolling(4).std()
    df = df.dropna().reset_index(drop=True)

    feature_cols = [f"{target}_lag_{lag}" for lag in range(1, lag_count + 1)] + [
        "rolling_mean_4",
        "rolling_std_4",
        "listings_count",
        "avg_km",
        "avg_age",
        "vintage_share",
        "youngtimer_share",
        "two_stroke_share",
    ]
    feature_cols += [col for col in ["riding_season_share"] if col in df.columns]
    feature_cols += ["month", "week_number"]

    return df, feature_cols


def chronological_split(df, test_size=0.2):
    """Time-aware train/test split preserving temporal order.

    Args:
        df: Sorted DataFrame.
        test_size: Fraction of data to use as test set.

    Returns:
        Tuple of (train_df, test_df).

    Raises:
        ValueError: If fewer than 10 observations remain.
    """
    if len(df) < 10:
        raise ValueError("At least 10 observations are required after feature engineering")
    split_idx = int(len(df) * (1 - test_size))
    split_idx = min(max(split_idx, 1), len(df) - 1)
    return df.iloc[:split_idx].copy(), df.iloc[split_idx:].copy()
