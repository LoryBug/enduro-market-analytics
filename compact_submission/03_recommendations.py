"""Create general and future cluster-level buying recommendations."""

import matplotlib.pyplot as plt
import pandas as pd

import utils as u


FUTURE_START = "2026-06-30"
FUTURE_END = "2026-12-31"


def general_buying_period_recommendation():
    """Build general buying period recommendations from best model predictions."""
    predictions_path = u.OUTPUT_TABLES / "predictions.csv"
    metrics_path = u.OUTPUT_TABLES / "metrics.csv"
    if not predictions_path.exists() or not metrics_path.exists():
        raise FileNotFoundError("Run 02_forecasting.py before recommendations")
    predictions = pd.read_csv(predictions_path, parse_dates=["period"])
    metrics = pd.read_csv(metrics_path)
    best_model = metrics.sort_values("RMSE").iloc[0]["model"]
    historical_reference = predictions["actual"].median()
    recommendations = predictions[["period", "actual", best_model]].copy().rename(columns={best_model: "predicted_price"})
    recommendations["expected_saving_vs_median"] = historical_reference - recommendations["predicted_price"]
    recommendations["recommended"] = recommendations["expected_saving_vs_median"] > 0
    recommendations = recommendations.sort_values("expected_saving_vs_median", ascending=False)
    recommendations.to_csv(u.OUTPUT_TABLES / "buying_period_recommendations.csv", index=False)
    print(f"Best general model by RMSE: {best_model}")
    print(recommendations.head(10).to_string(index=False))


def select_best_model(model_series):
    """Select best cluster model by RMSE."""
    metrics, _predictions, feature_cols = u.evaluate_cluster_models(model_series)
    metrics = metrics.sort_values("RMSE")
    return metrics.iloc[0]["model"], metrics.iloc[0].to_dict(), feature_cols


def save_future_plot(recommendations):
    """Save future buy score heatmap."""
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
    fig.savefig(u.OUTPUT_FIGURES / "13_future_cluster_buy_windows.png", dpi=150)
    plt.close(fig)


def future_cluster_recommendations():
    """Forecast future months and rank cluster buying opportunities."""
    series_path = u.OUTPUT_TABLES / "age_km_monthly_cluster_series.csv"
    if not series_path.exists():
        raise FileNotFoundError("Run 01_preprocess_descriptive.py first")
    series = pd.read_csv(series_path, parse_dates=["period"])
    future_periods = pd.date_range(FUTURE_START, FUTURE_END, freq="M")
    rows = []
    model_rows = []
    for cluster_id in u.eligible_clusters(series)["cluster_id"]:
        cluster = u.prepare_model_series(series[series["cluster_id"] == cluster_id])
        best_model, best_metrics, feature_cols = select_best_model(cluster)
        forecasts = u.forecast_future(cluster, best_model, feature_cols, future_periods)
        historical_median = cluster.loc[cluster["listings_count"] > 0, "median_price"].median()
        model_rows.append({"cluster_id": cluster_id, "best_model": best_model, **best_metrics})
        for period, forecast in zip(future_periods, forecasts):
            score = historical_median - forecast
            score_pct = score / historical_median * 100 if historical_median else 0
            rows.append({"cluster_id": cluster_id, "period": period, "predicted_median_price": forecast, "historical_cluster_median": historical_median, "buy_score": score, "buy_score_pct": score_pct, "recommendation": u.label_future_recommendation(score_pct), "model_used": best_model})
    recommendations = pd.DataFrame(rows).sort_values(["buy_score", "period"], ascending=[False, True])
    model_selection = pd.DataFrame(model_rows).sort_values("cluster_id")
    recommendations.to_csv(u.OUTPUT_TABLES / "future_cluster_buy_recommendations.csv", index=False)
    model_selection.to_csv(u.OUTPUT_TABLES / "future_cluster_model_selection.csv", index=False)
    save_future_plot(recommendations)
    print(recommendations.head(12).to_string(index=False))


def main():
    """Generate all recommendation outputs."""
    u.ensure_output_dirs()
    general_buying_period_recommendation()
    future_cluster_recommendations()


if __name__ == "__main__":
    main()
