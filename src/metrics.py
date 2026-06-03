import numpy as np
import pandas as pd
from math import comb


def mae(y_true, y_pred):
    return float(np.mean(np.abs(np.asarray(y_true) - np.asarray(y_pred))))


def rmse(y_true, y_pred):
    return float(np.sqrt(np.mean((np.asarray(y_true) - np.asarray(y_pred)) ** 2)))


def mape(y_true, y_pred):
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    mask = y_true != 0
    if not np.any(mask):
        return np.nan
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100)


def r2_score_manual(y_true, y_pred):
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    if ss_tot == 0:
        return np.nan
    return float(1 - ss_res / ss_tot)


def regression_metrics(y_true, y_pred, model_name):
    return {
        "model": model_name,
        "MAE": mae(y_true, y_pred),
        "RMSE": rmse(y_true, y_pred),
        "MAPE": mape(y_true, y_pred),
        "R2": r2_score_manual(y_true, y_pred),
    }


def save_metrics(rows, path):
    df = pd.DataFrame(rows).sort_values("RMSE")
    df.to_csv(path, index=False)
    return df


def exact_sign_test_p_value(wins_a, wins_b):
    n = int(wins_a + wins_b)
    if n == 0:
        return 1.0
    tail = min(int(wins_a), int(wins_b))
    probability = sum(comb(n, k) for k in range(tail + 1)) / (2**n)
    return float(min(1.0, 2 * probability))


def compare_absolute_errors(predictions, actual_col="actual"):
    model_cols = [col for col in predictions.columns if col not in {"period", actual_col}]
    rows = []
    actual = predictions[actual_col].to_numpy(dtype=float)

    for idx, model_a in enumerate(model_cols):
        error_a = np.abs(actual - predictions[model_a].to_numpy(dtype=float))
        for model_b in model_cols[idx + 1 :]:
            error_b = np.abs(actual - predictions[model_b].to_numpy(dtype=float))
            wins_a = int(np.sum(error_a < error_b))
            wins_b = int(np.sum(error_b < error_a))
            ties = int(np.sum(error_a == error_b))
            mean_abs_error_diff = float(np.mean(error_a - error_b))
            if mean_abs_error_diff < 0:
                better_model = model_a
            elif mean_abs_error_diff > 0:
                better_model = model_b
            else:
                better_model = "tie"

            rows.append(
                {
                    "model_a": model_a,
                    "model_b": model_b,
                    "better_model_by_mean_abs_error": better_model,
                    "mean_abs_error_diff_a_minus_b": mean_abs_error_diff,
                    "wins_a": wins_a,
                    "wins_b": wins_b,
                    "ties": ties,
                    "sign_test_p_value": exact_sign_test_p_value(wins_a, wins_b),
                }
            )

    return pd.DataFrame(rows).sort_values("sign_test_p_value")
