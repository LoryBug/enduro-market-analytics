import numpy as np
import pandas as pd
from math import comb


def mae(y_true, y_pred):
    """Mean Absolute Error.

    Args:
        y_true: Ground truth values.
        y_pred: Predicted values.

    Returns:
        MAE as float.
    """
    return float(np.mean(np.abs(np.asarray(y_true) - np.asarray(y_pred))))


def rmse(y_true, y_pred):
    """Root Mean Squared Error.

    Penalises larger errors more heavily than MAE.

    Args:
        y_true: Ground truth values.
        y_pred: Predicted values.

    Returns:
        RMSE as float.
    """
    return float(np.sqrt(np.mean((np.asarray(y_true) - np.asarray(y_pred)) ** 2)))


def mape(y_true, y_pred):
    """Mean Absolute Percentage Error.

    Ignores zero actual values to avoid division by zero.

    Args:
        y_true: Ground truth values.
        y_pred: Predicted values.

    Returns:
        MAPE as a percentage float, or NaN if all actuals are zero.
    """
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    mask = y_true != 0
    if not np.any(mask):
        return np.nan
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100)


def r2_score_manual(y_true, y_pred):
    """Coefficient of determination (R²) computed manually.

    Args:
        y_true: Ground truth values.
        y_pred: Predicted values.

    Returns:
        R² score as float, or NaN if total sum of squares is zero.
    """
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    if ss_tot == 0:
        return np.nan
    return float(1 - ss_res / ss_tot)


def regression_metrics(y_true, y_pred, model_name):
    """Compute all four metrics (MAE, RMSE, MAPE, R²) in one dict.

    Args:
        y_true: Ground truth values.
        y_pred: Predicted values.
        model_name: Label for the model.

    Returns:
        Dict with keys 'model', 'MAE', 'RMSE', 'MAPE', 'R2'.
    """
    return {
        "model": model_name,
        "MAE": mae(y_true, y_pred),
        "RMSE": rmse(y_true, y_pred),
        "MAPE": mape(y_true, y_pred),
        "R2": r2_score_manual(y_true, y_pred),
    }


def save_metrics(rows, path):
    """Sort metrics by RMSE and save to CSV.

    Args:
        rows: List of metric dicts (from regression_metrics).
        path: Output CSV path.

    Returns:
        Sorted DataFrame.
    """
    df = pd.DataFrame(rows).sort_values("RMSE")
    df.to_csv(path, index=False)
    return df


def exact_sign_test_p_value(wins_a, wins_b):
    """Two-sided exact binomial sign test p-value.

    Tests whether model A significantly outperforms model B based on
    per-period absolute error comparisons.

    Args:
        wins_a: Number of periods where model A had lower error.
        wins_b: Number of periods where model B had lower error.

    Returns:
        Two-sided p-value.
    """
    n = int(wins_a + wins_b)
    if n == 0:
        return 1.0
    tail = min(int(wins_a), int(wins_b))
    probability = sum(comb(n, k) for k in range(tail + 1)) / (2**n)
    return float(min(1.0, 2 * probability))


def compare_absolute_errors(predictions, actual_col="actual"):
    """Pairwise model comparison via absolute errors and sign test.

    For every pair of models, computes wins, ties, mean error difference,
    and the sign test p-value.

    Args:
        predictions: DataFrame with 'period', actual_col, and model columns.
        actual_col: Name of the column holding actual values.

    Returns:
        DataFrame with rows of pairwise comparisons sorted by p-value.
    """
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
