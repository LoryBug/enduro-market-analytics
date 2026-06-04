import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import DATA_PROCESSED, OUTPUT_FIGURES, OUTPUT_TABLES, PROCESSED_LISTINGS, RAW_LISTINGS, WEEKLY_SERIES, MONTHLY_SERIES
from src.plots import save_market_series_by_type, save_price_distribution, save_price_vs_age, save_seasonal_market_summary
from src.preprocessing import build_monthly_market_series, build_seasonal_market_summary, build_weekly_market_series, clean_listings, load_raw_listings


def main():
    """Load raw listings, clean, engineer features, build time series and seasonal summary."""
    if not RAW_LISTINGS.exists():
        raise FileNotFoundError(
            f"Missing raw dataset: {RAW_LISTINGS}. Copy the template and fill it with collected listings."
        )

    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    OUTPUT_FIGURES.mkdir(parents=True, exist_ok=True)
    OUTPUT_TABLES.mkdir(parents=True, exist_ok=True)

    raw = load_raw_listings(RAW_LISTINGS)
    clean = clean_listings(raw)
    weekly = build_weekly_market_series(clean)
    monthly = build_monthly_market_series(clean)
    seasonal = build_seasonal_market_summary(clean)

    clean.to_csv(PROCESSED_LISTINGS, index=False)
    weekly.to_csv(WEEKLY_SERIES, index=False)
    monthly.to_csv(MONTHLY_SERIES, index=False)
    seasonal.to_csv(OUTPUT_TABLES / "seasonal_market_summary.csv", index=False)

    save_price_distribution(clean, OUTPUT_FIGURES / "01_price_distribution.png")
    save_price_vs_age(clean, OUTPUT_FIGURES / "02_price_vs_age.png")
    save_market_series_by_type(clean, "price", "W", OUTPUT_FIGURES / "03_weekly_median_price.png")
    save_market_series_by_type(clean, "price", "M", OUTPUT_FIGURES / "04_monthly_median_price.png")
    save_seasonal_market_summary(seasonal, OUTPUT_FIGURES / "14_seasonal_market_summary.png")

    print(f"Raw listings: {len(raw)}")
    print(f"Clean listings: {len(clean)}")
    print(f"Weekly observations: {len(weekly)}")
    print(f"Monthly observations: {len(monthly)}")
    print(f"Saved: {PROCESSED_LISTINGS}")
    print(f"Saved: {WEEKLY_SERIES}")
    print(f"Saved: {MONTHLY_SERIES}")
    print(f"Saved: {OUTPUT_TABLES / 'seasonal_market_summary.csv'}")


if __name__ == "__main__":
    main()
