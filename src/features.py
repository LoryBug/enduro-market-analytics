import pandas as pd


def make_lagged_features(series_df, target, lag_count=4):
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
        "month",
        "week_number",
    ]

    return df, feature_cols


def chronological_split(df, test_size=0.2):
    if len(df) < 10:
        raise ValueError("At least 10 observations are required after feature engineering")
    split_idx = int(len(df) * (1 - test_size))
    split_idx = min(max(split_idx, 1), len(df) - 1)
    return df.iloc[:split_idx].copy(), df.iloc[split_idx:].copy()
