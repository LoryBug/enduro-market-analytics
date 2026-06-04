import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

try:
    from statsmodels.tsa.holtwinters import ExponentialSmoothing, SimpleExpSmoothing
except ImportError:  # Keeps the project executable when statsmodels is not installed.
    ExponentialSmoothing = None
    SimpleExpSmoothing = None


def seasonal_naive_forecast(train_values, horizon, season_length=4):
    """Baseline forecast: repeat the most recent seasonal pattern.

    Args:
        train_values: 1-D array of training target values.
        horizon: Number of steps to forecast.
        season_length: Length of the seasonal pattern to repeat.

    Returns:
        Array of forecast values.
    """
    train_values = np.asarray(train_values, dtype=float)
    if len(train_values) >= season_length:
        pattern = train_values[-season_length:]
    else:
        pattern = train_values[-1:]
    return np.resize(pattern, horizon)


def holt_winters_forecast(train_values, horizon, season_length=4):
    """Holt-Winters exponential smoothing with additive trend and seasonality.

    Falls back to simple exponential smoothing if statsmodels is unavailable
    or if the series is too short. Falls back to seasonal naive on error.

    Args:
        train_values: 1-D array of training target values.
        horizon: Number of steps to forecast.
        season_length: Seasonal period length.

    Returns:
        Array of forecast values.
    """
    train_values = np.asarray(train_values, dtype=float)
    if ExponentialSmoothing is None or SimpleExpSmoothing is None:
        return simple_exponential_smoothing_forecast(train_values, horizon)

    try:
        if len(train_values) >= season_length * 2:
            model = ExponentialSmoothing(
                train_values,
                trend="add",
                seasonal="add",
                seasonal_periods=season_length,
                initialization_method="estimated",
            )
        else:
            model = SimpleExpSmoothing(train_values, initialization_method="estimated")
        fitted = model.fit(optimized=True)
        return np.asarray(fitted.forecast(horizon), dtype=float)
    except Exception:
        return seasonal_naive_forecast(train_values, horizon, season_length)


def simple_exponential_smoothing_forecast(train_values, horizon, alpha=0.35):
    """Manual simple exponential smoothing fallback.

    Used when statsmodels is not available.

    Args:
        train_values: 1-D array of training target values.
        horizon: Number of steps to forecast.
        alpha: Smoothing factor.

    Returns:
        Array of constant forecast values.
    """
    train_values = np.asarray(train_values, dtype=float)
    level = train_values[0]
    for value in train_values[1:]:
        level = alpha * value + (1 - alpha) * level
    return np.repeat(level, horizon)


def train_random_forest(X_train, y_train):
    """Train a Random Forest regressor with tuned hyperparameters.

    Args:
        X_train: Feature matrix for training.
        y_train: Target vector for training.

    Returns:
        Fitted RandomForestRegressor.
    """
    model = RandomForestRegressor(
        n_estimators=300,
        max_depth=8,
        min_samples_leaf=2,
        random_state=42,
    )
    model.fit(X_train, y_train)
    return model


def train_mlp(X_train, y_train):
    """Train an MLP regressor with StandardScaler pipeline.

    Uses two hidden layers (32, 16), ReLU activation, Adam solver,
    and early stopping.

    Args:
        X_train: Feature matrix for training.
        y_train: Target vector for training.

    Returns:
        Fitted Pipeline (scaler + MLP).
    """
    model = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            (
                "mlp",
                MLPRegressor(
                    hidden_layer_sizes=(32, 16),
                    activation="relu",
                    solver="adam",
                    max_iter=2000,
                    early_stopping=True,
                    random_state=42,
                ),
            ),
        ]
    )
    model.fit(X_train, y_train)
    return model
