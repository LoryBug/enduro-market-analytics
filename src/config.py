"""Project-wide configuration: paths, constants, thresholds."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
OUTPUT_FIGURES = PROJECT_ROOT / "outputs" / "figures"
OUTPUT_TABLES = PROJECT_ROOT / "outputs" / "tables"

RAW_LISTINGS = DATA_RAW / "enduro_listings_raw.csv"
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
