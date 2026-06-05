"""Train general and cluster forecasting models."""

import matplotlib.pyplot as plt
import pandas as pd

import utils as u


def load_market_series():
    """Load monthly market series for general forecasting."""
    if not u.MONTHLY_SERIES.exists():
        raise FileNotFoundError("Run 01_preprocess_descriptive.py before forecasting")
    return pd.read_csv(u.MONTHLY_SERIES, parse_dates=["period"])


def train_general_forecast():
    """Train and compare general market forecasting models."""
    series = load_market_series()
    supervised, feature_cols = u.make_lagged_features(series, u.FORECAST_TARGET, u.LAG_COUNT)
    train, test = u.chronological_split(supervised, u.TEST_SIZE)
    x_train = train[feature_cols]
    y_train = train[u.FORECAST_TARGET]
    x_test = test[feature_cols]
    y_test = test[u.FORECAST_TARGET]
    horizon = len(test)
    predictions = pd.DataFrame({"period": test["period"], "actual": y_test.values})
    metrics_rows = []
    pred_baseline = u.seasonal_naive_forecast(y_train.values, horizon, season_length=min(4, len(y_train)))
    predictions["seasonal_naive"] = pred_baseline
    metrics_rows.append(u.regression_metrics(y_test, pred_baseline, "seasonal_naive"))
    pred_hw = u.holt_winters_forecast(y_train.values, horizon, season_length=min(4, len(y_train)))
    predictions["holt_winters"] = pred_hw
    metrics_rows.append(u.regression_metrics(y_test, pred_hw, "holt_winters"))
    rf = u.train_random_forest(x_train, y_train)
    pred_rf = rf.predict(x_test)
    predictions["random_forest"] = pred_rf
    metrics_rows.append(u.regression_metrics(y_test, pred_rf, "random_forest"))
    mlp = u.train_mlp(x_train, y_train)
    pred_mlp = mlp.predict(x_test)
    predictions["mlp"] = pred_mlp
    metrics_rows.append(u.regression_metrics(y_test, pred_mlp, "mlp"))
    metrics_df = u.save_metrics(metrics_rows, u.OUTPUT_TABLES / "metrics.csv")
    predictions.to_csv(u.OUTPUT_TABLES / "predictions.csv", index=False)
    comparison = u.compare_absolute_errors(predictions)
    comparison.to_csv(u.OUTPUT_TABLES / "model_comparison_tests.csv", index=False)
    u.save_forecast_comparison(predictions, u.FORECAST_TARGET, u.OUTPUT_FIGURES / "05_forecast_comparison.png")
    u.save_metrics_bar(metrics_df, u.OUTPUT_FIGURES / "06_model_rmse_comparison.png")
    print(metrics_df.to_string(index=False))


def forecast_cluster(cluster_df, cluster_id):
    """Forecast one cluster and return metrics and predictions."""
    model_series = u.prepare_model_series(cluster_df)
    metrics_df, predictions, _feature_cols = u.evaluate_cluster_models(model_series)
    if metrics_df is None:
        return None, None
    predictions.insert(0, "cluster_id", cluster_id)
    metrics_df["cluster_id"] = cluster_id
    return metrics_df[["cluster_id", "model", "MAE", "RMSE", "MAPE", "R2"]], predictions


def save_cluster_metrics_plot(metrics):
    """Save best cluster model MAPE plot."""
    best = metrics.sort_values(["cluster_id", "RMSE"]).groupby("cluster_id").first().reset_index()
    plt.figure(figsize=(11, 5.5))
    labels = best["cluster_id"].str.replace("__", " / ")
    bars = plt.bar(labels, best["MAPE"], color="#2563eb")
    plt.xticks(rotation=35, ha="right")
    plt.ylabel("Best MAPE (%)")
    plt.title("Forecast accuracy by age/km cluster - lower is better")
    plt.grid(axis="y", alpha=0.25)
    plt.ylim(0, best["MAPE"].max() * 1.25)
    for bar, model, rmse in zip(bars, best["model"], best["RMSE"]):
        plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), f"{model}\nRMSE {rmse:.0f}", ha="center", va="bottom", fontsize=8.5)
    plt.tight_layout()
    plt.savefig(u.OUTPUT_FIGURES / "11_cluster_forecast_rmse.png", dpi=150)
    plt.close()


def save_buy_score_plot(scores):
    """Save current cluster buy score plot."""
    plt.figure(figsize=(11, 5.5))
    labels = scores["cluster_id"].str.replace("__", " / ")
    colors = ["#16a34a" if value > 0 else "#dc2626" for value in scores["buy_score"]]
    plt.bar(labels, scores["buy_score"], color=colors)
    plt.axhline(0, color="#111827", linewidth=1)
    plt.xticks(rotation=35, ha="right")
    plt.ylabel("EUR below/above historical cluster median")
    plt.title("Latest buying score by age/km cluster")
    plt.grid(axis="y", alpha=0.25)
    plt.tight_layout()
    plt.savefig(u.OUTPUT_FIGURES / "12_cluster_buy_score.png", dpi=150)
    plt.close()


def train_cluster_forecasts():
    """Forecast eligible age/km clusters and save scores."""
    series_path = u.OUTPUT_TABLES / "age_km_monthly_cluster_series.csv"
    if not series_path.exists():
        raise FileNotFoundError("Run 01_preprocess_descriptive.py before cluster forecasting")
    series = pd.read_csv(series_path, parse_dates=["period"])
    eligible = u.eligible_clusters(series)
    all_metrics = []
    all_predictions = []
    for cluster_id in eligible["cluster_id"]:
        cluster_df = series[series["cluster_id"] == cluster_id]
        metrics, predictions = forecast_cluster(cluster_df, cluster_id)
        if metrics is not None:
            all_metrics.append(metrics)
            all_predictions.append(predictions)
    if not all_metrics:
        raise ValueError("No cluster has enough observations for forecasting")
    metrics_df = pd.concat(all_metrics, ignore_index=True).sort_values(["cluster_id", "RMSE"])
    predictions_df = pd.concat(all_predictions, ignore_index=True)
    scores = u.build_cluster_buying_scores(series, metrics_df)
    eligible.to_csv(u.OUTPUT_TABLES / "cluster_forecast_eligible_clusters.csv", index=False)
    metrics_df.to_csv(u.OUTPUT_TABLES / "cluster_forecast_metrics.csv", index=False)
    predictions_df.to_csv(u.OUTPUT_TABLES / "cluster_forecast_predictions.csv", index=False)
    scores.to_csv(u.OUTPUT_TABLES / "cluster_buying_scores.csv", index=False)
    save_cluster_metrics_plot(metrics_df)
    save_buy_score_plot(scores)
    print(f"Eligible clusters: {len(eligible)}")
    print(f"Forecasted clusters: {metrics_df['cluster_id'].nunique()}")
    print(metrics_df.sort_values("RMSE").head(10).to_string(index=False))


def main():
    """Run general and cluster forecasting."""
    u.ensure_output_dirs()
    train_general_forecast()
    train_cluster_forecasts()


if __name__ == "__main__":
    main()
