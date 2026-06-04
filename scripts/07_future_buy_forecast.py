import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.cluster_forecasting import eligible_clusters, evaluate_cluster_models, forecast_future, label_future_recommendation, prepare_model_series
from src.config import OUTPUT_FIGURES, OUTPUT_TABLES


SERIES_PATH = OUTPUT_TABLES / "age_km_monthly_cluster_series.csv"
FUTURE_START = "2026-06-30"
FUTURE_END = "2026-12-31"


def select_best_model(model_series):
    """Evaluate models on a cluster and return the best one by RMSE."""
    metrics, _predictions, feature_cols = evaluate_cluster_models(model_series)
    metrics = metrics.sort_values("RMSE")
    return metrics.iloc[0]["model"], metrics.iloc[0].to_dict(), feature_cols


def save_future_plot(recommendations):
    """Save heatmap of future buy scores across clusters and months."""
    plot_df = recommendations.copy()
    plot_df["month_label"] = plot_df["period"].dt.strftime("%Y-%m")
    plot_df["cluster_label"] = plot_df["cluster_id"].str.replace("__", " / ")
    order = plot_df.groupby("cluster_label")["buy_score"].max().sort_values(ascending=False).index
    matrix = plot_df.pivot(index="cluster_label", columns="month_label", values="buy_score").reindex(order)

    fig, ax = plt.subplots(figsize=(11.5, 5.5))
    limit = max(abs(matrix.min().min()), abs(matrix.max().max()))
    image = ax.imshow(matrix.values, cmap="RdYlGn", vmin=-limit, vmax=limit, aspect="auto")
    ax.set_xticks(range(len(matrix.columns)), matrix.columns, rotation=35, ha="right")
    ax.set_yticks(range(len(matrix.index)), matrix.index)
    ax.set_title("Future buy score heatmap by age/km cluster")
    ax.set_xlabel("Forecast month")
    ax.set_ylabel("Cluster")
    for row_idx, cluster in enumerate(matrix.index):
        for col_idx, month in enumerate(matrix.columns):
            value = matrix.loc[cluster, month]
            if pd.notna(value):
                ax.text(col_idx, row_idx, f"{value:+.0f}", ha="center", va="center", fontsize=9, color="#111827")
    fig.colorbar(image, ax=ax, label="Expected saving vs cluster median (EUR)")
    fig.tight_layout()
    fig.savefig(OUTPUT_FIGURES / "13_future_cluster_buy_windows.png", dpi=150)
    plt.close(fig)


def main():
    """Forecast future months per cluster, compute buy scores, and save recommendations."""
    OUTPUT_TABLES.mkdir(parents=True, exist_ok=True)
    OUTPUT_FIGURES.mkdir(parents=True, exist_ok=True)
    if not SERIES_PATH.exists():
        raise FileNotFoundError("Run scripts/05_age_km_market_insights.py first")

    series = pd.read_csv(SERIES_PATH, parse_dates=["period"])
    future_periods = pd.date_range(FUTURE_START, FUTURE_END, freq="M")
    rows = []
    model_rows = []

    for cluster_id in eligible_clusters(series)["cluster_id"]:
        cluster = prepare_model_series(series[series["cluster_id"] == cluster_id])
        best_model, best_metrics, feature_cols = select_best_model(cluster)
        forecasts = forecast_future(cluster, best_model, feature_cols, future_periods)
        historical_median = cluster.loc[cluster["listings_count"] > 0, "median_price"].median()
        model_rows.append({"cluster_id": cluster_id, "best_model": best_model, **best_metrics})

        for period, forecast in zip(future_periods, forecasts):
            score = historical_median - forecast
            score_pct = score / historical_median * 100 if historical_median else 0
            rows.append(
                {
                    "cluster_id": cluster_id,
                    "period": period,
                    "predicted_median_price": forecast,
                    "historical_cluster_median": historical_median,
                    "buy_score": score,
                    "buy_score_pct": score_pct,
                    "recommendation": label_future_recommendation(score_pct),
                    "model_used": best_model,
                }
            )

    recommendations = pd.DataFrame(rows).sort_values(["buy_score", "period"], ascending=[False, True])
    model_selection = pd.DataFrame(model_rows).sort_values("cluster_id")
    recommendations.to_csv(OUTPUT_TABLES / "future_cluster_buy_recommendations.csv", index=False)
    model_selection.to_csv(OUTPUT_TABLES / "future_cluster_model_selection.csv", index=False)
    save_future_plot(recommendations)

    print(recommendations.head(12).to_string(index=False))
    print(f"Saved: {OUTPUT_TABLES / 'future_cluster_buy_recommendations.csv'}")
    print(f"Saved: {OUTPUT_TABLES / 'future_cluster_model_selection.csv'}")
    print(f"Saved: {OUTPUT_FIGURES / '13_future_cluster_buy_windows.png'}")


if __name__ == "__main__":
    main()
