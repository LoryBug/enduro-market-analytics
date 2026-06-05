"""Shared utilities for the compact Enduro Market Analytics submission."""

from math import comb
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Rectangle
from sklearn.ensemble import RandomForestRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

try:
    from statsmodels.tsa.holtwinters import ExponentialSmoothing, SimpleExpSmoothing
except ImportError:
    ExponentialSmoothing = None
    SimpleExpSmoothing = None


PROJECT_ROOT = Path(__file__).resolve().parent
RAW_LISTINGS = PROJECT_ROOT / "enduro_listings_raw.csv"
DATA_PROCESSED = PROJECT_ROOT / "data_processed"
OUTPUT_FIGURES = PROJECT_ROOT / "outputs_figures"
OUTPUT_TABLES = PROJECT_ROOT / "outputs_tables"

PROCESSED_LISTINGS = DATA_PROCESSED / "enduro_listings_clean.csv"
WEEKLY_SERIES = DATA_PROCESSED / "weekly_market_series.csv"
MONTHLY_SERIES = DATA_PROCESSED / "monthly_market_series.csv"
CORE_MONTHLY_SERIES = DATA_PROCESSED / "core_modern_enduro_monthly_series.csv"

CURRENT_YEAR = 2026
FORECAST_TARGET = "median_price"
TEST_SIZE = 0.2
LAG_COUNT = 4
CORE_MIN_CC = 250
CORE_MAX_CC = 500
CORE_MIN_PRICE = 1000
CORE_MAX_PRICE = 20000
AGE_BINS = [-1, 2, 5, 10, 20, 100]
AGE_LABELS = ["0-2", "3-5", "6-10", "11-20", "20+"]
KM_BINS = [-1, 5_000, 10_000, 15_000, 1_000_000]
KM_LABELS = ["0-5k", "5-10k", "10-15k", "15k+"]
MIN_CLUSTER_COUNT = 20
MIN_CLUSTER_MONTHS = 20
MIN_LISTINGS_PER_MONTH = 10

REQUIRED_COLUMNS = [
    "listing_date",
    "source",
    "brand",
    "model",
    "year",
    "km",
    "engine_cc",
    "price",
    "region",
    "province",
    "seller_type",
    "is_2stroke",
    "condition_score",
    "has_documents",
]

SEASON_ORDER = {"winter": 1, "spring": 2, "summer": 3, "autumn": 4}
SEGMENT_COLORS = {
    "core modern 250-500": "#2563eb",
    "maxi 690/701": "#7c3aed",
    "other modern": "#38bdf8",
    "youngtimer": "#f59e0b",
    "vintage": "#dc2626",
}


def ensure_output_dirs():
    """Create all runtime output directories."""
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    OUTPUT_FIGURES.mkdir(parents=True, exist_ok=True)
    OUTPUT_TABLES.mkdir(parents=True, exist_ok=True)


def load_raw_listings(path=RAW_LISTINGS):
    """Load raw listings CSV and validate required columns.

    Args:
        path: Path to the raw CSV file.

    Returns:
        Raw listings DataFrame.
    """
    df = pd.read_csv(path)
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    return df


def _to_numeric(series):
    """Convert a Series to numeric, handling Italian number formatting."""
    if pd.api.types.is_numeric_dtype(series):
        return pd.to_numeric(series, errors="coerce")
    cleaned = series.astype(str).str.replace(r"[^0-9.,-]", "", regex=True)
    cleaned = cleaned.str.replace(r"\.0$", "", regex=True)
    cleaned = cleaned.str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
    return pd.to_numeric(cleaned, errors="coerce")


def clean_listings(df):
    """Clean raw listings and create analytical features.

    Args:
        df: Raw listings DataFrame.

    Returns:
        Clean listings DataFrame sorted by observation date.
    """
    df = df.copy()
    df["listing_date"] = pd.to_datetime(df["listing_date"], errors="coerce")
    if "snapshot_date" in df.columns:
        df["snapshot_date"] = pd.to_datetime(df["snapshot_date"], errors="coerce")
    for col in ["year", "km", "engine_cc", "price", "condition_score"]:
        df[col] = _to_numeric(df[col])
    for col in ["brand", "model", "source", "region", "province", "seller_type"]:
        df[col] = df[col].astype(str).str.strip().str.lower()
    for col in ["is_2stroke", "has_documents"]:
        df[col] = df[col].astype(str).str.strip().str.lower().isin(["1", "true", "yes", "y", "si", "si"])
    df = df.dropna(subset=["listing_date", "year", "price"])
    df = df[(df["price"] > 0) & (df["year"] >= 1960) & (df["year"] <= CURRENT_YEAR)]
    df["age"] = (CURRENT_YEAR - df["year"]).clip(lower=0)
    df["km_per_year"] = df["km"] / df["age"].replace(0, 1)
    df["price_per_cc"] = df["price"] / df["engine_cc"].replace(0, np.nan)
    df["is_vintage"] = df["year"] < 1995
    df["is_youngtimer"] = (df["year"] >= 1995) & (df["year"] < 2010)
    df["market_segment"] = np.select([df["is_vintage"], df["is_youngtimer"]], ["vintage", "youngtimer"], default="modern")
    df["observation_date"] = df["listing_date"]
    add_seasonal_features(df)
    return df.sort_values("observation_date").reset_index(drop=True)


def add_seasonal_features(df):
    """Add season and riding_season columns from observation_date."""
    month = df["observation_date"].dt.month
    df["season"] = np.select(
        [month.isin([12, 1, 2]), month.isin([3, 4, 5]), month.isin([6, 7, 8])],
        ["winter", "spring", "summer"],
        default="autumn",
    )
    df["riding_season"] = month.between(4, 10)
    return df


def summarize_market_groups(df, group_col, group_type):
    """Aggregate market indicators for a categorical group."""
    summary = (
        df.groupby(group_col)
        .agg(
            listings_count=("price", "size"),
            median_price=("price", "median"),
            avg_price=("price", "mean"),
            q25_price=("price", lambda value: value.quantile(0.25)),
            q75_price=("price", lambda value: value.quantile(0.75)),
            avg_km=("km", "mean"),
            avg_age=("age", "mean"),
        )
        .reset_index()
        .rename(columns={group_col: "period_label"})
    )
    summary.insert(0, "group_type", group_type)
    return summary


def build_seasonal_market_summary(df):
    """Build seasonal and riding-period market summary table."""
    season_summary = summarize_market_groups(df, "season", "season")
    season_summary["sort_order"] = season_summary["period_label"].map(SEASON_ORDER)
    riding_df = df.copy()
    riding_df["riding_period"] = np.where(riding_df["riding_season"], "riding_season_apr_oct", "off_season_nov_mar")
    riding_summary = summarize_market_groups(riding_df, "riding_period", "riding_period")
    riding_summary["sort_order"] = riding_summary["period_label"].map({"riding_season_apr_oct": 1, "off_season_nov_mar": 2})
    summary = pd.concat([season_summary, riding_summary], ignore_index=True)
    return summary.sort_values(["group_type", "sort_order"]).drop(columns="sort_order").reset_index(drop=True)


def build_market_series(df, frequency="W"):
    """Aggregate listings into weekly or monthly market series."""
    if df.empty:
        raise ValueError("Cannot build market series from an empty listings dataset")
    series = (
        df.set_index("observation_date")
        .resample(frequency)
        .agg(
            avg_price=("price", "mean"),
            median_price=("price", "median"),
            listings_count=("price", "count"),
            avg_km=("km", "mean"),
            avg_age=("age", "mean"),
            vintage_share=("is_vintage", "mean"),
            youngtimer_share=("is_youngtimer", "mean"),
            two_stroke_share=("is_2stroke", "mean"),
        )
        .reset_index()
        .rename(columns={"observation_date": "period"})
    )
    series = series[series["listings_count"] > 0].copy()
    series["week_number"] = series["period"].dt.isocalendar().week.astype(int)
    series["month"] = series["period"].dt.month
    return series


def build_weekly_market_series(df):
    """Aggregate listings to weekly market series."""
    return build_market_series(df, frequency="W")


def build_monthly_market_series(df):
    """Aggregate listings to monthly market series."""
    return build_market_series(df, frequency="M")


def add_motorcycle_type(df):
    """Add plot-friendly motorcycle_type category."""
    plot_df = df.copy()
    plot_df["motorcycle_type"] = "other modern"
    plot_df.loc[plot_df["market_segment"] == "youngtimer", "motorcycle_type"] = "youngtimer"
    plot_df.loc[plot_df["market_segment"] == "vintage", "motorcycle_type"] = "vintage"
    plot_df.loc[plot_df["engine_cc"].isin([690, 701]), "motorcycle_type"] = "maxi 690/701"
    core_mask = (
        (plot_df["market_segment"] == "modern")
        & plot_df["engine_cc"].between(250, 500)
        & plot_df["price"].between(1000, 20000)
    )
    plot_df.loc[core_mask, "motorcycle_type"] = "core modern 250-500"
    return plot_df


def save_price_distribution(df, path):
    """Save price distribution histogram by motorcycle type."""
    fig, ax = plt.subplots(figsize=(9, 5.2))
    plot_df = add_motorcycle_type(df).dropna(subset=["price"])
    prices = plot_df["price"]
    median_price = prices.median()
    mean_price = prices.mean()
    x_limit = prices.quantile(0.99)
    hidden_outliers = int((prices > x_limit).sum())
    for motorcycle_type, group in plot_df.groupby("motorcycle_type"):
        central_prices = group.loc[group["price"] <= x_limit, "price"]
        if central_prices.empty:
            continue
        ax.hist(central_prices, bins=24, alpha=0.42, edgecolor="white", label=f"{motorcycle_type} (n={len(group)})", color=SEGMENT_COLORS.get(motorcycle_type, "#64748b"))
    ax.axvline(median_price, color="#111827", linewidth=2.2, label=f"Median: EUR {median_price:,.0f}".replace(",", "."))
    ax.axvline(mean_price, color="#2563eb", linewidth=1.8, linestyle="--", label=f"Mean: EUR {mean_price:,.0f}".replace(",", "."))
    ax.text(0.98, 0.78, f"Top 1% outliers hidden from x-axis: {hidden_outliers}", transform=ax.transAxes, ha="right", fontsize=9, color="#475569")
    ax.set_title("Price distribution by motorcycle type")
    ax.set_xlabel("Asking price (EUR)")
    ax.set_ylabel("Listings count")
    ax.grid(axis="y", alpha=0.22)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def save_price_vs_age(df, path):
    """Save scatter plot of asking price versus bike age."""
    fig, ax = plt.subplots(figsize=(9, 5.2))
    plot_df = add_motorcycle_type(df).dropna(subset=["age", "price"]).copy()
    y_limit = plot_df["price"].quantile(0.99)
    hidden_outliers = int((plot_df["price"] > y_limit).sum())
    for motorcycle_type, group in plot_df.groupby("motorcycle_type"):
        ax.scatter(group["age"], group["price"], color=SEGMENT_COLORS.get(motorcycle_type, "#64748b"), alpha=0.45, s=24, edgecolors="none", label=motorcycle_type)
    core = plot_df[(plot_df["motorcycle_type"] == "core modern 250-500") & (plot_df["price"] <= y_limit)]
    if len(core) >= 2:
        coeffs = np.polyfit(core["age"], core["price"], deg=1)
        x_values = np.linspace(core["age"].min(), core["age"].max(), 100)
        ax.plot(x_values, coeffs[0] * x_values + coeffs[1], color="#111827", linewidth=2.2, label="Trend, core modern 250-500")
    ax.set_title("Price vs age by motorcycle type")
    ax.set_xlabel("Bike age (years)")
    ax.set_ylabel("Asking price (EUR)")
    ax.set_ylim(0, y_limit * 1.05)
    ax.text(0.98, 0.9, f"Top 1% price outliers hidden from y-axis: {hidden_outliers}", transform=ax.transAxes, ha="right", fontsize=9, color="#475569")
    ax.grid(alpha=0.22)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def save_market_series_by_type(df, target, freq, path):
    """Save smoothed median price series by motorcycle type."""
    plot_df = add_motorcycle_type(df).dropna(subset=["observation_date", target]).copy()
    plot_df["period"] = plot_df["observation_date"].dt.to_period(freq).dt.to_timestamp("W" if freq == "W" else "M")
    grouped = plot_df.groupby(["motorcycle_type", "period"]).agg(median_price=(target, "median"), listings_count=(target, "size")).reset_index()
    fig, ax = plt.subplots(figsize=(11, 5.5))
    for motorcycle_type, group in grouped.groupby("motorcycle_type"):
        if group["listings_count"].sum() < 20:
            continue
        group = group.sort_values("period")
        smoothed = group.set_index("period")["median_price"].rolling(3, min_periods=1).median()
        ax.plot(smoothed.index, smoothed.values, linewidth=2, label=motorcycle_type, color=SEGMENT_COLORS.get(motorcycle_type, "#64748b"))
    label = "weekly" if freq == "W" else "monthly"
    ax.set_title(f"{label.title()} median price by motorcycle type - 3-period smoothing")
    ax.set_xlabel("Period")
    ax.set_ylabel("Median price (EUR)")
    ax.grid(alpha=0.22)
    ax.legend(fontsize=8)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def save_seasonal_market_summary(summary, path):
    """Save bar chart of listings and median price by season."""
    plot_df = summary.copy()
    plot_df["label"] = plot_df["period_label"].replace(
        {"riding_season_apr_oct": "Riding\nApr-Oct", "off_season_nov_mar": "Off-season\nNov-Mar", "winter": "Winter", "spring": "Spring", "summer": "Summer", "autumn": "Autumn"}
    )
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.2))
    colors = ["#2563eb" if group == "riding_period" else "#f59e0b" for group in plot_df["group_type"]]
    axes[0].bar(plot_df["label"], plot_df["listings_count"], color=colors)
    axes[0].set_title("Listings by season")
    axes[0].set_ylabel("Listings count")
    axes[0].tick_params(axis="x", rotation=20)
    axes[0].grid(axis="y", alpha=0.22)
    axes[1].bar(plot_df["label"], plot_df["median_price"], color=colors)
    axes[1].set_title("Median price by season")
    axes[1].set_ylabel("Median price (EUR)")
    axes[1].tick_params(axis="x", rotation=20)
    axes[1].grid(axis="y", alpha=0.22)
    for ax, value_col in zip(axes, ["listings_count", "median_price"]):
        for idx, value in enumerate(plot_df[value_col]):
            ax.text(idx, value, f"{value:,.0f}".replace(",", "."), ha="center", va="bottom", fontsize=8.5)
    fig.suptitle("Seasonal market summary")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def save_core_plot(monthly):
    """Save plot comparing full market and core market monthly medians."""
    core = monthly[monthly["selected_segment"] == "core_modern_enduro_250_500"].copy()
    full = monthly[monthly["selected_segment"] == "full_market"].copy()
    reliable = core[core["is_reliable_month"]]
    weak = core[~core["is_reliable_month"]]
    plt.figure(figsize=(12, 6))
    plt.plot(full["period"], full["median_price"], color="#cbd5e1", linewidth=1.4, label="Full market monthly median")
    full_smooth = full.set_index("period")["median_price"].rolling(3, min_periods=1).median()
    plt.plot(full_smooth.index, full_smooth.values, color="#94a3b8", linewidth=2, linestyle="--", label="Full market 3-month median")
    plt.plot(core["period"], core["median_price"], color="#fed7aa", linewidth=1.5, label="Core monthly median")
    plt.scatter(weak["period"], weak["median_price"], color="#f59e0b", s=30, label="Core < 10 listings")
    plt.scatter(reliable["period"], reliable["median_price"], color="#2563eb", s=36, label="Core >= 10 listings")
    if not reliable.empty:
        rolling = reliable.set_index("period")["median_price"].rolling(3, min_periods=1).median()
        plt.plot(rolling.index, rolling.values, color="#111827", linewidth=2.4, label="Core reliable 3-month median")
    plt.title("Why segment selection matters: full market vs core modern enduro 250-500cc")
    plt.xlabel("Month")
    plt.ylabel("Median price (EUR)")
    plt.grid(alpha=0.25)
    plt.legend(loc="upper left", bbox_to_anchor=(1.01, 1), borderaxespad=0)
    plt.tight_layout()
    plt.savefig(OUTPUT_FIGURES / "07_selected_core_monthly_median.png", dpi=150)
    plt.close()


def save_heatmap(matrix, count_matrix, path):
    """Save annotated age/km median price heatmap."""
    fig, ax = plt.subplots(figsize=(9, 5.8))
    values = matrix.to_numpy(dtype=float)
    image = ax.imshow(np.ma.masked_invalid(values), cmap="YlOrRd")
    ax.set_xticks(range(len(KM_LABELS)), KM_LABELS)
    ax.set_yticks(range(len(AGE_LABELS)), AGE_LABELS)
    ax.set_xlabel("Km band")
    ax.set_ylabel("Age band")
    ax.set_title("Median price by age and mileage band - Core modern enduro 250-500cc")
    for row_idx, age_label in enumerate(AGE_LABELS):
        for col_idx, km_label in enumerate(KM_LABELS):
            price = matrix.loc[age_label, km_label]
            count = count_matrix.loc[age_label, km_label]
            if pd.isna(price):
                text = "n.d."
            else:
                status = "strong" if count >= MIN_CLUSTER_COUNT else "weak"
                text = f"EUR {price:,.0f}\nn={int(count)} {status}".replace(",", ".")
                if count < MIN_CLUSTER_COUNT:
                    ax.add_patch(Rectangle((col_idx - 0.5, row_idx - 0.5), 1, 1, fill=False, edgecolor="#111827", linewidth=1.4, linestyle="--"))
            ax.text(col_idx, row_idx, text, ha="center", va="center", fontsize=8.6, color="#111827")
    fig.colorbar(image, ax=ax, label="Median price (EUR)")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def save_band_boxplot(core, dimension, path):
    """Save boxplot of prices by age band or km band."""
    labels = AGE_LABELS if dimension == "age_band" else KM_LABELS
    title = "Price distribution by age band" if dimension == "age_band" else "Price distribution by mileage band"
    xlabel = "Age band (years)" if dimension == "age_band" else "Km band"
    data = [core.loc[core[dimension].astype(str) == label, "price"].dropna() for label in labels]
    non_empty = [(label, values) for label, values in zip(labels, data) if len(values) > 0]
    plot_labels = [item[0] for item in non_empty]
    plot_data = [item[1] for item in non_empty]
    fig, ax = plt.subplots(figsize=(8.8, 5.2))
    ax.boxplot(plot_data, labels=plot_labels, showfliers=False, patch_artist=True, medianprops={"color": "#111827", "linewidth": 2}, boxprops={"facecolor": "#fed7aa", "color": "#ea580c"}, whiskerprops={"color": "#ea580c"}, capprops={"color": "#ea580c"})
    for idx, values in enumerate(plot_data, start=1):
        median = values.median()
        ax.text(idx, median, f"n={len(values)}\nEUR {median:,.0f}".replace(",", "."), ha="center", va="bottom", fontsize=8.5, color="#111827")
    ax.set_title(f"{title} - core modern enduro 250-500cc")
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Asking price (EUR)")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def make_lagged_features(series_df, target, lag_count=4):
    """Create lagged target, rolling stats and feature list."""
    df = series_df.copy().sort_values("period")
    for lag in range(1, lag_count + 1):
        df[f"{target}_lag_{lag}"] = df[target].shift(lag)
    df["rolling_mean_4"] = df[target].shift(1).rolling(4).mean()
    df["rolling_std_4"] = df[target].shift(1).rolling(4).std()
    df = df.dropna().reset_index(drop=True)
    feature_cols = [f"{target}_lag_{lag}" for lag in range(1, lag_count + 1)] + ["rolling_mean_4", "rolling_std_4", "listings_count", "avg_km", "avg_age", "vintage_share", "youngtimer_share", "two_stroke_share"]
    feature_cols += [col for col in ["riding_season_share"] if col in df.columns]
    feature_cols += ["month", "week_number"]
    return df, feature_cols


def chronological_split(df, test_size=0.2):
    """Split a sorted DataFrame into chronological train/test subsets."""
    if len(df) < 10:
        raise ValueError("At least 10 observations are required after feature engineering")
    split_idx = int(len(df) * (1 - test_size))
    split_idx = min(max(split_idx, 1), len(df) - 1)
    return df.iloc[:split_idx].copy(), df.iloc[split_idx:].copy()


def seasonal_naive_forecast(train_values, horizon, season_length=4):
    """Repeat the most recent seasonal pattern as forecast."""
    train_values = np.asarray(train_values, dtype=float)
    pattern = train_values[-season_length:] if len(train_values) >= season_length else train_values[-1:]
    return np.resize(pattern, horizon)


def simple_exponential_smoothing_forecast(train_values, horizon, alpha=0.35):
    """Manual simple exponential smoothing fallback."""
    train_values = np.asarray(train_values, dtype=float)
    level = train_values[0]
    for value in train_values[1:]:
        level = alpha * value + (1 - alpha) * level
    return np.repeat(level, horizon)


def holt_winters_forecast(train_values, horizon, season_length=4):
    """Forecast with Holt-Winters, falling back safely on short/error cases."""
    train_values = np.asarray(train_values, dtype=float)
    if ExponentialSmoothing is None or SimpleExpSmoothing is None:
        return simple_exponential_smoothing_forecast(train_values, horizon)
    try:
        if len(train_values) >= season_length * 2:
            model = ExponentialSmoothing(train_values, trend="add", seasonal="add", seasonal_periods=season_length, initialization_method="estimated")
        else:
            model = SimpleExpSmoothing(train_values, initialization_method="estimated")
        return np.asarray(model.fit(optimized=True).forecast(horizon), dtype=float)
    except Exception:
        return seasonal_naive_forecast(train_values, horizon, season_length)


def train_random_forest(X_train, y_train):
    """Train the Random Forest regressor used in forecasts."""
    model = RandomForestRegressor(n_estimators=300, max_depth=8, min_samples_leaf=2, random_state=42)
    model.fit(X_train, y_train)
    return model


def train_mlp(X_train, y_train):
    """Train the scaled MLP regressor used as neural comparison."""
    model = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            ("mlp", MLPRegressor(hidden_layer_sizes=(32, 16), activation="relu", solver="adam", max_iter=2000, early_stopping=True, random_state=42)),
        ]
    )
    model.fit(X_train, y_train)
    return model


def mae(y_true, y_pred):
    """Mean absolute error."""
    return float(np.mean(np.abs(np.asarray(y_true) - np.asarray(y_pred))))


def rmse(y_true, y_pred):
    """Root mean squared error."""
    return float(np.sqrt(np.mean((np.asarray(y_true) - np.asarray(y_pred)) ** 2)))


def mape(y_true, y_pred):
    """Mean absolute percentage error."""
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    mask = y_true != 0
    if not np.any(mask):
        return np.nan
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100)


def r2_score_manual(y_true, y_pred):
    """Manual R2 score calculation."""
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    return np.nan if ss_tot == 0 else float(1 - ss_res / ss_tot)


def regression_metrics(y_true, y_pred, model_name):
    """Return MAE, RMSE, MAPE and R2 for one model."""
    return {"model": model_name, "MAE": mae(y_true, y_pred), "RMSE": rmse(y_true, y_pred), "MAPE": mape(y_true, y_pred), "R2": r2_score_manual(y_true, y_pred)}


def save_metrics(rows, path):
    """Save model metrics sorted by RMSE."""
    df = pd.DataFrame(rows).sort_values("RMSE")
    df.to_csv(path, index=False)
    return df


def exact_sign_test_p_value(wins_a, wins_b):
    """Two-sided exact sign-test p-value."""
    n = int(wins_a + wins_b)
    if n == 0:
        return 1.0
    tail = min(int(wins_a), int(wins_b))
    probability = sum(comb(n, k) for k in range(tail + 1)) / (2**n)
    return float(min(1.0, 2 * probability))


def compare_absolute_errors(predictions, actual_col="actual"):
    """Compare model absolute errors pairwise and run sign tests."""
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
            mean_diff = float(np.mean(error_a - error_b))
            better = model_a if mean_diff < 0 else model_b if mean_diff > 0 else "tie"
            rows.append({"model_a": model_a, "model_b": model_b, "better_model_by_mean_abs_error": better, "mean_abs_error_diff_a_minus_b": mean_diff, "wins_a": wins_a, "wins_b": wins_b, "ties": ties, "sign_test_p_value": exact_sign_test_p_value(wins_a, wins_b)})
    return pd.DataFrame(rows).sort_values("sign_test_p_value")


def filter_core_market(df):
    """Filter to modern 250-500cc core enduro listings."""
    return df[(df["market_segment"] == "modern") & (df["engine_cc"].between(CORE_MIN_CC, CORE_MAX_CC)) & (df["price"].between(CORE_MIN_PRICE, CORE_MAX_PRICE))].copy()


def add_age_km_bands(df):
    """Add age_band and km_band columns."""
    df = df.copy()
    df["age_band"] = pd.cut(df["age"], bins=AGE_BINS, labels=AGE_LABELS)
    df["km_band"] = pd.cut(df["km"], bins=KM_BINS, labels=KM_LABELS)
    return df


def add_cluster_id(df):
    """Add cluster_id as age_band__km_band."""
    df = df.copy()
    df["cluster_id"] = df["age_band"].astype(str) + "__" + df["km_band"].astype(str)
    return df


def build_cluster_summary(core):
    """Compute price and coverage summary per age/km cluster."""
    grouped = (
        core.groupby(["age_band", "km_band"], observed=False)
        .agg(
            listings_count=("price", "size"),
            median_price=("price", "median"),
            avg_price=("price", "mean"),
            q25_price=("price", lambda value: value.quantile(0.25) if len(value) else np.nan),
            q75_price=("price", lambda value: value.quantile(0.75) if len(value) else np.nan),
            min_price=("price", "min"),
            max_price=("price", "max"),
            avg_age=("age", "mean"),
            avg_km=("km", "mean"),
        )
        .reset_index()
    )
    grouped["iqr_price"] = grouped["q75_price"] - grouped["q25_price"]
    grouped["coverage_status"] = np.select([grouped["listings_count"] >= MIN_CLUSTER_COUNT, grouped["listings_count"] > 0], ["strong", "weak"], default="empty")
    grouped["needs_more_observations"] = grouped["listings_count"].between(1, MIN_CLUSTER_COUNT - 1)
    grouped["rows_needed_to_min20"] = (MIN_CLUSTER_COUNT - grouped["listings_count"]).clip(lower=0)
    return grouped


def build_price_matrix(summary):
    """Pivot median prices to age x km matrix."""
    return summary.pivot(index="age_band", columns="km_band", values="median_price").reindex(index=AGE_LABELS, columns=KM_LABELS)


def build_count_matrix(summary):
    """Pivot listing counts to age x km matrix."""
    return summary.pivot(index="age_band", columns="km_band", values="listings_count").reindex(index=AGE_LABELS, columns=KM_LABELS)


def build_monthly_cluster_series(core):
    """Build monthly cluster time series from observed months only."""
    core = core.copy()
    core["period"] = core["observation_date"].dt.to_period("M").dt.to_timestamp("M")
    monthly = (
        core.groupby(["age_band", "km_band", "period"], observed=True)
        .agg(median_price=("price", "median"), avg_price=("price", "mean"), listings_count=("price", "size"), avg_km=("km", "mean"), avg_age=("age", "mean"))
        .reset_index()
    )
    monthly = add_cluster_id(monthly)
    monthly["week_number"] = monthly["period"].dt.isocalendar().week.astype(int)
    monthly["month"] = monthly["period"].dt.month
    monthly["riding_season_share"] = monthly["month"].between(4, 10).astype(float)
    return monthly.sort_values(["cluster_id", "period"]).reset_index(drop=True)


def build_buying_advice(summary):
    """Create descriptive buying advice by age/km cluster."""
    usable = summary[summary["listings_count"] > 0].copy()
    baseline = usable.loc[usable["listings_count"] >= MIN_CLUSTER_COUNT, "median_price"].median()
    if pd.isna(baseline):
        baseline = usable["median_price"].median()
    usable["discount_vs_core_baseline"] = baseline - usable["median_price"]
    usable["relative_discount_pct"] = usable["discount_vs_core_baseline"] / baseline * 100
    usable["value_label"] = np.select([usable["relative_discount_pct"] >= 20, usable["relative_discount_pct"] >= 8, usable["relative_discount_pct"] <= -15], ["cheap", "fair", "expensive"], default="normal")
    usable["buying_note"] = usable.apply(make_buying_note, axis=1)
    cols = ["age_band", "km_band", "listings_count", "coverage_status", "median_price", "q25_price", "q75_price", "discount_vs_core_baseline", "relative_discount_pct", "value_label", "buying_note"]
    return usable[cols].sort_values(["value_label", "relative_discount_pct"], ascending=[True, False])


def make_buying_note(row):
    """Generate a brief descriptive note for one cluster."""
    if row["coverage_status"] == "weak":
        return "Interpret with caution: few listings in this cluster."
    if row["value_label"] == "cheap":
        return "Convenient cluster: median price well below core baseline."
    if row["value_label"] == "fair":
        return "Good compromise: below baseline with enough coverage."
    if row["value_label"] == "expensive":
        return "Expensive cluster: relevant only for very recent/specific bikes."
    return "Normal cluster relative to core market baseline."


TARGET = "median_price"
CLUSTER_LAG_COUNT = 3
MIN_SUPERVISED_ROWS = 12


def eligible_clusters(series, min_months=MIN_CLUSTER_MONTHS):
    """Return clusters with enough observed months for forecasting."""
    coverage = series[series["listings_count"] > 0].groupby("cluster_id").agg(real_months=("period", "nunique"), total_listings=("listings_count", "sum")).reset_index()
    return coverage[coverage["real_months"] >= min_months].sort_values(["real_months", "total_listings"], ascending=False)


def prepare_model_series(cluster_df):
    """Add model-required feature columns to a cluster series."""
    df = cluster_df.copy().sort_values("period")
    df["vintage_share"] = 0.0
    df["youngtimer_share"] = 0.0
    df["two_stroke_share"] = 0.0
    if "riding_season_share" not in df.columns:
        df["riding_season_share"] = df["period"].dt.month.between(4, 10).astype(float)
    return df


def evaluate_cluster_models(model_series):
    """Evaluate baseline, Holt-Winters and Random Forest for one cluster."""
    supervised, feature_cols = make_lagged_features(model_series, TARGET, CLUSTER_LAG_COUNT)
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
    """Label current buy score percentage."""
    if score_pct >= 10:
        return "good_buy_window"
    if score_pct >= 3:
        return "slightly_convenient"
    if score_pct <= -10:
        return "expensive_window"
    return "neutral"


def build_cluster_buying_scores(series, metrics):
    """Compute current buying scores by cluster."""
    best_models = metrics.sort_values(["cluster_id", "RMSE"]).groupby("cluster_id").first().reset_index()
    rows = []
    for _, best in best_models.iterrows():
        cluster_id = best["cluster_id"]
        cluster = series[series["cluster_id"] == cluster_id].sort_values("period")
        latest = cluster.iloc[-1]
        historical_median = cluster.loc[cluster["listings_count"] > 0, TARGET].median()
        score = historical_median - latest[TARGET]
        score_pct = score / historical_median * 100 if historical_median else 0
        rows.append({"cluster_id": cluster_id, "latest_period": latest["period"].date().isoformat(), "latest_median_price": latest[TARGET], "historical_cluster_median": historical_median, "buy_score": score, "buy_score_pct": score_pct, "best_model": best["model"], "best_rmse": best["RMSE"], "best_mape": best["MAPE"], "recommendation": label_recommendation(score_pct)})
    return pd.DataFrame(rows).sort_values("buy_score", ascending=False)


def recursive_random_forest_forecast(model_series, feature_cols, future_periods):
    """Forecast future periods recursively with Random Forest."""
    supervised, _ = make_lagged_features(model_series, TARGET, CLUSTER_LAG_COUNT)
    rf = train_random_forest(supervised[feature_cols], supervised[TARGET])
    history = model_series[TARGET].tolist()
    recent_exog = model_series.tail(6)
    forecasts = []
    for period in future_periods:
        row = {f"{TARGET}_lag_{lag}": history[-lag] for lag in range(1, CLUSTER_LAG_COUNT + 1)}
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
    """Forecast future periods using the selected best model."""
    values = model_series[TARGET].values
    horizon = len(future_periods)
    if best_model == "seasonal_naive":
        return seasonal_naive_forecast(values, horizon, season_length=min(4, len(values)))
    if best_model == "holt_winters":
        return holt_winters_forecast(values, horizon, season_length=min(4, len(values)))
    return recursive_random_forest_forecast(model_series, feature_cols, future_periods)


def label_future_recommendation(score_pct):
    """Label future buy score percentage."""
    if score_pct >= 10:
        return "strong_buy"
    if score_pct >= 3:
        return "good_buy"
    if score_pct <= -10:
        return "avoid_expensive"
    return "neutral"


def save_forecast_comparison(predictions, target, path):
    """Save actual-vs-predicted comparison plot."""
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(predictions["period"], predictions["actual"], marker="o", label="Actual")
    for col in predictions.columns:
        if col not in ["period", "actual"]:
            ax.plot(predictions["period"], predictions[col], marker="o", linestyle="--", label=col)
    ax.set_title(f"General market forecast comparison - {target}")
    ax.set_xlabel("Month")
    ax.set_ylabel(f"{target} (EUR)")
    ax.grid(alpha=0.22)
    ax.legend()
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def save_metrics_bar(metrics_df, path):
    """Save RMSE comparison bar chart."""
    metrics_df = metrics_df.sort_values("RMSE")
    fig, ax = plt.subplots(figsize=(8.5, 5))
    bars = ax.bar(metrics_df["model"], metrics_df["RMSE"], color=["#16a34a", "#2563eb", "#f59e0b", "#dc2626"][: len(metrics_df)])
    ax.set_title("General forecast error by model")
    ax.set_xlabel("Model")
    ax.set_ylabel("RMSE (EUR)")
    ax.tick_params(axis="x", rotation=20)
    ax.grid(axis="y", alpha=0.22)
    for bar, value in zip(bars, metrics_df["MAPE"]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), f"MAPE {value:.1f}%", ha="center", va="bottom", fontsize=9)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
