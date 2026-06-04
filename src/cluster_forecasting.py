import numpy as np
import pandas as pd

from .config import MIN_CLUSTER_MONTHS, TEST_SIZE
from .features import chronological_split, make_lagged_features
from .metrics import regression_metrics
from .models import holt_winters_forecast, seasonal_naive_forecast, train_random_forest


TARGET = "median_price"
LAG_COUNT = 3
MIN_SUPERVISED_ROWS = 12


def eligible_clusters(series, min_months=MIN_CLUSTER_MONTHS):
    coverage = (
        series[series["listings_count"] > 0]
        .groupby("cluster_id")
        .agg(real_months=("period", "nunique"), total_listings=("listings_count", "sum"))
        .reset_index()
    )
    return coverage[coverage["real_months"] >= min_months].sort_values(["real_months", "total_listings"], ascending=False)


def prepare_model_series(cluster_df):
    df = cluster_df.copy().sort_values("period")
    df["vintage_share"] = 0.0
    df["youngtimer_share"] = 0.0
    df["two_stroke_share"] = 0.0
    if "riding_season_share" not in df.columns:
        df["riding_season_share"] = df["period"].dt.month.between(4, 10).astype(float)
    return df


def evaluate_cluster_models(model_series):
    supervised, feature_cols = make_lagged_features(model_series, TARGET, LAG_COUNT)
    if len(supervised) < MIN_SUPERVISED_ROWS:
        return None, None, None

    train, test = chronological_split(supervised, TEST_SIZE)
    horizon = len(test)
    y_train = train[TARGET]
    y_test = test[TARGET]
    predictions = pd.DataFrame({"period": test["period"], "actual": y_test.values})
    metrics = []

    pred_baseline = seasonal_naive_forecast(y_train.values, horizon, season_length=min(4, len(y_train)))
    predictions["seasonal_naive"] = pred_baseline
    metrics.append(regression_metrics(y_test, pred_baseline, "seasonal_naive"))

    pred_hw = holt_winters_forecast(y_train.values, horizon, season_length=min(4, len(y_train)))
    predictions["holt_winters"] = pred_hw
    metrics.append(regression_metrics(y_test, pred_hw, "holt_winters"))

    rf = train_random_forest(train[feature_cols], y_train)
    pred_rf = rf.predict(test[feature_cols])
    predictions["random_forest"] = pred_rf
    metrics.append(regression_metrics(y_test, pred_rf, "random_forest"))

    return pd.DataFrame(metrics), predictions, feature_cols


def label_recommendation(score_pct):
    if score_pct >= 10:
        return "good_buy_window"
    if score_pct >= 3:
        return "slightly_convenient"
    if score_pct <= -10:
        return "expensive_window"
    return "neutral"


def build_cluster_buying_scores(series, metrics):
    best_models = metrics.sort_values(["cluster_id", "RMSE"]).groupby("cluster_id").first().reset_index()
    rows = []
    for _, best in best_models.iterrows():
        cluster_id = best["cluster_id"]
        cluster = series[series["cluster_id"] == cluster_id].sort_values("period")
        latest = cluster.iloc[-1]
        historical_median = cluster.loc[cluster["listings_count"] > 0, TARGET].median()
        score = historical_median - latest[TARGET]
        score_pct = score / historical_median * 100 if historical_median else 0
        rows.append(
            {
                "cluster_id": cluster_id,
                "latest_period": latest["period"].date().isoformat(),
                "latest_median_price": latest[TARGET],
                "historical_cluster_median": historical_median,
                "buy_score": score,
                "buy_score_pct": score_pct,
                "best_model": best["model"],
                "best_rmse": best["RMSE"],
                "best_mape": best["MAPE"],
                "recommendation": label_recommendation(score_pct),
            }
        )
    return pd.DataFrame(rows).sort_values("buy_score", ascending=False)


def recursive_random_forest_forecast(model_series, feature_cols, future_periods):
    supervised, _ = make_lagged_features(model_series, TARGET, LAG_COUNT)
    rf = train_random_forest(supervised[feature_cols], supervised[TARGET])
    history = model_series[TARGET].tolist()
    recent_exog = model_series.tail(6)
    forecasts = []

    for period in future_periods:
        row = {}
        for lag in range(1, LAG_COUNT + 1):
            row[f"{TARGET}_lag_{lag}"] = history[-lag]
        previous = pd.Series(history[-4:])
        row["rolling_mean_4"] = previous.mean()
        row["rolling_std_4"] = previous.std()
        row["listings_count"] = max(1, int(round(recent_exog["listings_count"].replace(0, np.nan).dropna().mean() or 1)))
        row["avg_km"] = recent_exog["avg_km"].mean()
        row["avg_age"] = recent_exog["avg_age"].mean() + len(forecasts) / 12
        row["vintage_share"] = 0.0
        row["youngtimer_share"] = 0.0
        row["two_stroke_share"] = 0.0
        row["riding_season_share"] = float(4 <= period.month <= 10)
        row["month"] = period.month
        row["week_number"] = int(period.isocalendar().week)
        prediction = float(rf.predict(pd.DataFrame([row])[feature_cols])[0])
        forecasts.append(prediction)
        history.append(prediction)

    return forecasts


def forecast_future(model_series, best_model, feature_cols, future_periods):
    values = model_series[TARGET].values
    horizon = len(future_periods)
    if best_model == "seasonal_naive":
        return seasonal_naive_forecast(values, horizon, season_length=min(4, len(values)))
    if best_model == "holt_winters":
        return holt_winters_forecast(values, horizon, season_length=min(4, len(values)))
    return recursive_random_forest_forecast(model_series, feature_cols, future_periods)


def label_future_recommendation(score_pct):
    if score_pct >= 10:
        return "strong_buy"
    if score_pct >= 3:
        return "good_buy"
    if score_pct <= -10:
        return "avoid_expensive"
    return "neutral"
