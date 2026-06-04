import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import FORECAST_TARGET, OUTPUT_TABLES


def main():
    """Compare best-model predictions to historical median and flag good buying periods."""
    predictions_path = OUTPUT_TABLES / "predictions.csv"
    metrics_path = OUTPUT_TABLES / "metrics.csv"
    if not predictions_path.exists() or not metrics_path.exists():
        raise FileNotFoundError("Run scripts/02_train_forecasting_models.py before generating recommendations")

    predictions = pd.read_csv(predictions_path, parse_dates=["period"])
    metrics = pd.read_csv(metrics_path)
    best_model = metrics.sort_values("RMSE").iloc[0]["model"]

    historical_reference = predictions["actual"].median()
    recommendations = predictions[["period", "actual", best_model]].copy()
    recommendations = recommendations.rename(columns={best_model: "predicted_price"})
    recommendations["expected_saving_vs_median"] = historical_reference - recommendations["predicted_price"]
    recommendations["recommended"] = recommendations["expected_saving_vs_median"] > 0
    recommendations = recommendations.sort_values("expected_saving_vs_median", ascending=False)

    output_path = OUTPUT_TABLES / "buying_period_recommendations.csv"
    recommendations.to_csv(output_path, index=False)

    print(f"Best model by RMSE: {best_model}")
    print(recommendations.head(10).to_string(index=False))
    print(f"Saved recommendations: {output_path}")


if __name__ == "__main__":
    main()
