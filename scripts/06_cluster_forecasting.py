import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.cluster_forecasting import build_cluster_buying_scores, eligible_clusters, evaluate_cluster_models, prepare_model_series
from src.config import OUTPUT_FIGURES, OUTPUT_TABLES


SERIES_PATH = OUTPUT_TABLES / "age_km_monthly_cluster_series.csv"
def load_cluster_series():
    if not SERIES_PATH.exists():
        raise FileNotFoundError("Run scripts/05_age_km_market_insights.py before cluster forecasting")
    return pd.read_csv(SERIES_PATH, parse_dates=["period"])


def forecast_cluster(cluster_df, cluster_id):
    model_series = prepare_model_series(cluster_df)
    metrics_df, predictions, _feature_cols = evaluate_cluster_models(model_series)
    if metrics_df is None:
        return None, None
    predictions.insert(0, "cluster_id", cluster_id)
    metrics_df["cluster_id"] = cluster_id
    metrics_df = metrics_df[["cluster_id", "model", "MAE", "RMSE", "MAPE", "R2"]]
    return metrics_df, predictions


def save_cluster_metrics_plot(metrics):
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
    plt.savefig(OUTPUT_FIGURES / "11_cluster_forecast_rmse.png", dpi=150)
    plt.close()


def save_buy_score_plot(scores):
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
    plt.savefig(OUTPUT_FIGURES / "12_cluster_buy_score.png", dpi=150)
    plt.close()


def main():
    OUTPUT_TABLES.mkdir(parents=True, exist_ok=True)
    OUTPUT_FIGURES.mkdir(parents=True, exist_ok=True)
    series = load_cluster_series()
    eligible = eligible_clusters(series)

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
    scores = build_cluster_buying_scores(series, metrics_df)

    eligible.to_csv(OUTPUT_TABLES / "cluster_forecast_eligible_clusters.csv", index=False)
    metrics_df.to_csv(OUTPUT_TABLES / "cluster_forecast_metrics.csv", index=False)
    predictions_df.to_csv(OUTPUT_TABLES / "cluster_forecast_predictions.csv", index=False)
    scores.to_csv(OUTPUT_TABLES / "cluster_buying_scores.csv", index=False)
    save_cluster_metrics_plot(metrics_df)
    save_buy_score_plot(scores)

    print(f"Eligible clusters: {len(eligible)}")
    print(f"Forecasted clusters: {metrics_df['cluster_id'].nunique()}")
    print(metrics_df.sort_values("RMSE").head(10).to_string(index=False))
    print(f"Saved: {OUTPUT_TABLES / 'cluster_forecast_metrics.csv'}")
    print(f"Saved: {OUTPUT_TABLES / 'cluster_buying_scores.csv'}")


if __name__ == "__main__":
    main()
