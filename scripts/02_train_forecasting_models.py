import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import FORECAST_TARGET, LAG_COUNT, MONTHLY_SERIES, OUTPUT_FIGURES, OUTPUT_TABLES, TEST_SIZE, WEEKLY_SERIES
from src.features import chronological_split, make_lagged_features
from src.metrics import compare_absolute_errors, regression_metrics, save_metrics
from src.models import holt_winters_forecast, seasonal_naive_forecast, train_mlp, train_random_forest
from src.plots import save_forecast_comparison, save_metrics_bar


def load_series():
    # Monthly is preferred when the historical coverage is short.
    path = MONTHLY_SERIES if MONTHLY_SERIES.exists() else WEEKLY_SERIES
    if not path.exists():
        raise FileNotFoundError("Run scripts/01_preprocess.py before training models")
    df = pd.read_csv(path, parse_dates=["period"])
    print(f"Using market series: {path}")
    return df


def main():
    OUTPUT_TABLES.mkdir(parents=True, exist_ok=True)
    OUTPUT_FIGURES.mkdir(parents=True, exist_ok=True)

    series = load_series()
    supervised, feature_cols = make_lagged_features(series, FORECAST_TARGET, LAG_COUNT)
    train, test = chronological_split(supervised, TEST_SIZE)

    X_train = train[feature_cols]
    y_train = train[FORECAST_TARGET]
    X_test = test[feature_cols]
    y_test = test[FORECAST_TARGET]
    horizon = len(test)

    predictions = pd.DataFrame({"period": test["period"], "actual": y_test.values})
    metrics_rows = []

    pred_baseline = seasonal_naive_forecast(y_train.values, horizon, season_length=min(4, len(y_train)))
    predictions["seasonal_naive"] = pred_baseline
    metrics_rows.append(regression_metrics(y_test, pred_baseline, "seasonal_naive"))

    pred_hw = holt_winters_forecast(y_train.values, horizon, season_length=min(4, len(y_train)))
    predictions["holt_winters"] = pred_hw
    metrics_rows.append(regression_metrics(y_test, pred_hw, "holt_winters"))

    rf = train_random_forest(X_train, y_train)
    pred_rf = rf.predict(X_test)
    predictions["random_forest"] = pred_rf
    metrics_rows.append(regression_metrics(y_test, pred_rf, "random_forest"))

    mlp = train_mlp(X_train, y_train)
    pred_mlp = mlp.predict(X_test)
    predictions["mlp"] = pred_mlp
    metrics_rows.append(regression_metrics(y_test, pred_mlp, "mlp"))

    metrics_df = save_metrics(metrics_rows, OUTPUT_TABLES / "metrics.csv")
    predictions.to_csv(OUTPUT_TABLES / "predictions.csv", index=False)
    comparison_tests = compare_absolute_errors(predictions)
    comparison_tests.to_csv(OUTPUT_TABLES / "model_comparison_tests.csv", index=False)

    save_forecast_comparison(predictions, FORECAST_TARGET, OUTPUT_FIGURES / "05_forecast_comparison.png")
    save_metrics_bar(metrics_df, OUTPUT_FIGURES / "06_model_rmse_comparison.png")

    print(metrics_df.to_string(index=False))
    print(comparison_tests.to_string(index=False))
    print(f"Saved predictions: {OUTPUT_TABLES / 'predictions.csv'}")
    print(f"Saved metrics: {OUTPUT_TABLES / 'metrics.csv'}")
    print(f"Saved model comparison tests: {OUTPUT_TABLES / 'model_comparison_tests.csv'}")


if __name__ == "__main__":
    main()
