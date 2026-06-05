"""Clean listings and build descriptive market/cluster outputs."""

import pandas as pd

import utils as u


SEGMENTS = {
    "full_market": "All listings in the working dataset.",
    "core_modern_enduro_250_500": "Modern enduro listings, 250-500cc.",
    "maxi_enduro_690_701": "KTM 690 / Husqvarna 701 style enduro listings.",
    "vintage_epoca": "Vintage and youngtimer listings.",
}


def assign_selected_segments(df):
    """Create full/core/maxi/vintage segment copies."""
    full = df.copy()
    full["selected_segment"] = "full_market"
    core = u.filter_core_market(df)
    core["selected_segment"] = "core_modern_enduro_250_500"
    maxi = df[df["engine_cc"].isin([690, 701]) & df["price"].between(1000, 25000)].copy()
    maxi["selected_segment"] = "maxi_enduro_690_701"
    vintage = df[df["market_segment"].isin(["vintage", "youngtimer"]) & df["price"].between(500, 30000)].copy()
    vintage["selected_segment"] = "vintage_epoca"
    return pd.concat([full, core, maxi, vintage], ignore_index=True)


def monthly_medians(segmented):
    """Aggregate monthly medians per selected segment."""
    segmented = segmented.copy()
    segmented["period"] = segmented["observation_date"].dt.to_period("M").dt.to_timestamp("M")
    monthly = (
        segmented.groupby(["selected_segment", "period"])
        .agg(
            listings_count=("price", "size"),
            median_price=("price", "median"),
            avg_price=("price", "mean"),
            q25_price=("price", lambda value: value.quantile(0.25)),
            q75_price=("price", lambda value: value.quantile(0.75)),
            min_price=("price", "min"),
            max_price=("price", "max"),
            avg_age=("age", "mean"),
            avg_km=("km", "mean"),
        )
        .reset_index()
    )
    monthly["is_reliable_month"] = monthly["listings_count"] >= u.MIN_LISTINGS_PER_MONTH
    monthly["iqr_price"] = monthly["q75_price"] - monthly["q25_price"]
    return monthly


def segment_summary(monthly):
    """Summarize data coverage for each selected segment."""
    rows = []
    for segment, group in monthly.groupby("selected_segment"):
        reliable = group[group["is_reliable_month"]]
        rows.append(
            {
                "selected_segment": segment,
                "definition": SEGMENTS[segment],
                "months_with_data": len(group),
                "reliable_months_min10": len(reliable),
                "first_month": group["period"].min().date().isoformat(),
                "last_month": group["period"].max().date().isoformat(),
                "total_listings": int(group["listings_count"].sum()),
                "median_of_monthly_medians": reliable["median_price"].median() if not reliable.empty else group["median_price"].median(),
            }
        )
    return pd.DataFrame(rows).sort_values("selected_segment")


def save_core_processed_series(monthly):
    """Save the selected core monthly series for forecasting."""
    core = monthly[monthly["selected_segment"] == "core_modern_enduro_250_500"].copy()
    core["week_number"] = core["period"].dt.isocalendar().week.astype(int)
    core["month"] = core["period"].dt.month
    cols = ["period", "median_price", "avg_price", "listings_count", "avg_km", "avg_age", "q25_price", "q75_price", "iqr_price", "is_reliable_month", "week_number", "month"]
    core[cols].to_csv(u.CORE_MONTHLY_SERIES, index=False)


def preprocess_market():
    """Clean raw listings, build market time series and basic figures."""
    raw = u.load_raw_listings()
    clean = u.clean_listings(raw)
    weekly = u.build_weekly_market_series(clean)
    monthly = u.build_monthly_market_series(clean)
    seasonal = u.build_seasonal_market_summary(clean)
    clean.to_csv(u.PROCESSED_LISTINGS, index=False)
    weekly.to_csv(u.WEEKLY_SERIES, index=False)
    monthly.to_csv(u.MONTHLY_SERIES, index=False)
    seasonal.to_csv(u.OUTPUT_TABLES / "seasonal_market_summary.csv", index=False)
    u.save_price_distribution(clean, u.OUTPUT_FIGURES / "01_price_distribution.png")
    u.save_price_vs_age(clean, u.OUTPUT_FIGURES / "02_price_vs_age.png")
    u.save_market_series_by_type(clean, "price", "W", u.OUTPUT_FIGURES / "03_weekly_median_price.png")
    u.save_market_series_by_type(clean, "price", "M", u.OUTPUT_FIGURES / "04_monthly_median_price.png")
    u.save_seasonal_market_summary(seasonal, u.OUTPUT_FIGURES / "14_seasonal_market_summary.png")
    print(f"Raw listings: {len(raw)}")
    print(f"Clean listings: {len(clean)}")
    print(f"Weekly observations: {len(weekly)}")
    print(f"Monthly observations: {len(monthly)}")
    return clean


def analyze_segments(clean):
    """Build core segment selection outputs."""
    segmented = assign_selected_segments(clean)
    monthly = monthly_medians(segmented)
    summary = segment_summary(monthly)
    monthly.to_csv(u.OUTPUT_TABLES / "selected_monthly_medians.csv", index=False)
    summary.to_csv(u.OUTPUT_TABLES / "selected_market_summary.csv", index=False)
    save_core_processed_series(monthly)
    u.save_core_plot(monthly)
    print(f"Selected core listings: {len(segmented[segmented['selected_segment'] == 'core_modern_enduro_250_500'])}")


def analyze_age_km(clean):
    """Build age/km cluster summaries, matrices, advice and plots."""
    core = u.add_age_km_bands(u.filter_core_market(clean))
    core = core.dropna(subset=["age_band", "km_band", "price"])
    summary = u.build_cluster_summary(core)
    price_matrix = u.build_price_matrix(summary)
    count_matrix = u.build_count_matrix(summary)
    buying_advice = u.build_buying_advice(summary)
    monthly_cluster_series = u.build_monthly_cluster_series(core)
    summary.to_csv(u.OUTPUT_TABLES / "age_km_cluster_summary.csv", index=False)
    price_matrix.to_csv(u.OUTPUT_TABLES / "age_km_price_matrix.csv")
    count_matrix.to_csv(u.OUTPUT_TABLES / "age_km_count_matrix.csv")
    buying_advice.to_csv(u.OUTPUT_TABLES / "buying_advice_by_age_km.csv", index=False)
    monthly_cluster_series.to_csv(u.OUTPUT_TABLES / "age_km_monthly_cluster_series.csv", index=False)
    u.save_heatmap(price_matrix, count_matrix, u.OUTPUT_FIGURES / "08_age_km_price_heatmap.png")
    u.save_band_boxplot(core, "age_band", u.OUTPUT_FIGURES / "09_price_by_age_band.png")
    u.save_band_boxplot(core, "km_band", u.OUTPUT_FIGURES / "10_price_by_km_band.png")
    print(f"Core listings with age/km: {len(core)}")


def main():
    """Run preprocessing and descriptive analytics."""
    u.ensure_output_dirs()
    clean = preprocess_market()
    analyze_segments(clean)
    analyze_age_km(clean)


if __name__ == "__main__":
    main()
