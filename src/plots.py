import matplotlib.pyplot as plt
import numpy as np


SEGMENT_COLORS = {
    "core modern 250-500": "#2563eb",
    "maxi 690/701": "#7c3aed",
    "other modern": "#38bdf8",
    "youngtimer": "#f59e0b",
    "vintage": "#dc2626",
}


def add_motorcycle_type(df):
    """Classify each listing into a plot-friendly motorcycle type category.

    Categories: 'core modern 250-500', 'maxi 690/701', 'youngtimer',
    'vintage', or 'other modern'.

    Args:
        df: Listings DataFrame.

    Returns:
        DataFrame with added 'motorcycle_type' column.
    """
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
    """Save histogram of asking prices, coloured by motorcycle type.

    Overlays median and mean vertical lines. Hides the top 1% price
    outliers from the x-axis for readability.

    Args:
        df: Listings DataFrame.
        path: Output figure file path (PNG).
    """
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
        ax.hist(
            central_prices,
            bins=24,
            alpha=0.42,
            edgecolor="white",
            label=f"{motorcycle_type} (n={len(group)})",
            color=SEGMENT_COLORS.get(motorcycle_type, "#64748b"),
        )
    ax.axvline(median_price, color="#111827", linewidth=2.2, label=f"Mediana: EUR {median_price:,.0f}".replace(",", "."))
    ax.axvline(mean_price, color="#2563eb", linewidth=1.8, linestyle="--", label=f"Media: EUR {mean_price:,.0f}".replace(",", "."))
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
    """Save scatter plot of price vs age, coloured by motorcycle type.

    Includes a linear trend line for the core modern 250-500 segment.
    Hides top 1% price outliers for readability.

    Args:
        df: Listings DataFrame.
        path: Output figure file path (PNG).
    """
    fig, ax = plt.subplots(figsize=(9, 5.2))
    plot_df = add_motorcycle_type(df).dropna(subset=["age", "price"]).copy()
    y_limit = plot_df["price"].quantile(0.99)
    hidden_outliers = int((plot_df["price"] > y_limit).sum())
    for motorcycle_type, group in plot_df.groupby("motorcycle_type"):
        ax.scatter(
            group["age"],
            group["price"],
            color=SEGMENT_COLORS.get(motorcycle_type, "#64748b"),
            alpha=0.45,
            s=24,
            edgecolors="none",
            label=motorcycle_type,
        )

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


def save_market_series(series, target, path):
    """Save simple line plot of a market time series.

    Args:
        series: DataFrame with 'period' and target columns.
        target: Name of the column to plot.
        path: Output figure file path (PNG).
    """
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(series["period"], series[target], marker="o", linewidth=1.5, color="#2563eb")
    ax.set_title(f"Market time series: {target}")
    ax.set_xlabel("Period")
    ax.set_ylabel(f"{target} (EUR)")
    ax.grid(alpha=0.22)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def save_market_series_by_type(df, target, freq, path):
    """Save multi-line time series plot, one line per motorcycle type.

    Applies 3-period rolling median smoothing. Skips types with fewer
    than 20 total listings.

    Args:
        df: Listings DataFrame.
        target: Target column for median price aggregation.
        freq: Pandas offset string ('W' or 'M').
        path: Output figure file path (PNG).
    """
    plot_df = add_motorcycle_type(df).dropna(subset=["observation_date", target]).copy()
    plot_df["period"] = plot_df["observation_date"].dt.to_period(freq).dt.to_timestamp("W" if freq == "W" else "M")
    grouped = (
        plot_df.groupby(["motorcycle_type", "period"])
        .agg(median_price=(target, "median"), listings_count=(target, "size"))
        .reset_index()
    )

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
    """Save dual bar chart: listings count and median price by season.

    Displays both seasonal (winter/spring/summer/autumn) and riding-period
    (Apr-Oct vs Nov-Mar) groupings side by side.

    Args:
        summary: Seasonal market summary DataFrame.
        path: Output figure file path (PNG).
    """
    plot_df = summary.copy()
    plot_df["label"] = plot_df["period_label"].replace(
        {
            "riding_season_apr_oct": "Riding\nApr-Oct",
            "off_season_nov_mar": "Off-season\nNov-Mar",
            "winter": "Winter",
            "spring": "Spring",
            "summer": "Summer",
            "autumn": "Autumn",
        }
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
            label = f"{value:,.0f}".replace(",", ".")
            ax.text(idx, value, label, ha="center", va="bottom", fontsize=8.5)

    fig.suptitle("Seasonal market summary")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def save_forecast_comparison(predictions, target, path):
    """Save line plot comparing actual vs all model predictions.

    Args:
        predictions: DataFrame with 'period', 'actual', and model columns.
        target: Name of the target (used in title).
        path: Output figure file path (PNG).
    """
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
    """Save bar chart of RMSE by model, annotated with MAPE values.

    Args:
        metrics_df: DataFrame with 'model', 'RMSE', 'MAPE' columns.
        path: Output figure file path (PNG).
    """
    metrics_df = metrics_df.sort_values("RMSE")
    fig, ax = plt.subplots(figsize=(8.5, 5))
    bars = ax.bar(metrics_df["model"], metrics_df["RMSE"], color=["#16a34a", "#2563eb", "#f59e0b", "#dc2626"][: len(metrics_df)])
    ax.set_title("General forecast error by model")
    ax.set_xlabel("Model")
    ax.set_ylabel("RMSE (EUR)")
    ax.tick_params(axis="x", rotation=20)
    ax.grid(axis="y", alpha=0.22)
    for bar, mape in zip(bars, metrics_df["MAPE"]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), f"MAPE {mape:.1f}%", ha="center", va="bottom", fontsize=9)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
