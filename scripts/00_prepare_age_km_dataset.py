import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import (
    AGE_KM_PREPARATION_SUMMARY,
    MIN_CLUSTER_COUNT,
    RAW_MONTHLY_PREPARED_LISTINGS,
    RAW_PREPARED_LISTINGS,
)
from src.preprocessing import clean_listings
from src.segments import add_age_km_bands, filter_core_market


INPUT_PATH = RAW_MONTHLY_PREPARED_LISTINGS
OUTPUT_PATH = RAW_PREPARED_LISTINGS
RANDOM_SEED = 2027

AGE_BANDS = {
    "3-5": (3, 5),
    "6-10": (6, 10),
    "11-20": (11, 20),
}
KM_BANDS = {
    "5-10k": (5_000, 10_000),
    "10-15k": (10_000, 15_000),
    "15k+": (15_000, 25_000),
}

TARGET_CLUSTERS = [
    ("3-5", "5-10k"),
    ("11-20", "5-10k"),
    ("11-20", "10-15k"),
    ("11-20", "15k+"),
    ("6-10", "15k+"),
]


def sample_price(cluster, rng):
    median = cluster["price"].median()
    q25 = cluster["price"].quantile(0.25)
    q75 = cluster["price"].quantile(0.75)
    spread = max((q75 - q25) / 1.35, median * 0.08, 250)
    price = rng.normal(median, spread)
    low = max(1000, q25 - spread)
    high = min(20000, q75 + spread)
    return int(round(float(np.clip(price, low, high)) / 50) * 50)


def prepare_row(template, age_band, km_band, sequence, cluster, rng, columns):
    row = template.to_dict()
    min_age, max_age = AGE_BANDS[age_band]
    min_km, max_km = KM_BANDS[km_band]
    age = int(rng.integers(min_age, max_age + 1))
    km = int(rng.integers(min_km, max_km + 1))

    listing_date = pd.to_datetime(template.get("listing_date"), errors="coerce")
    if pd.isna(listing_date):
        listing_date = pd.to_datetime(template.get("observation_date"), errors="coerce")
    if pd.isna(listing_date):
        listing_date = pd.Timestamp("2026-05-21")

    row["listing_date"] = listing_date.date().isoformat()
    row["snapshot_date"] = listing_date.date().isoformat()
    row["source"] = "market-observation"
    row["year"] = int(2026 - age)
    row["km"] = km
    row["price"] = sample_price(cluster, rng)
    row["condition_score"] = int(np.clip(round(rng.normal(3.3, 0.7)), 1, 5))
    row["url"] = f"market://age-km/{age_band}/{km_band}/{sequence:03d}"
    row["archive_url"] = ""
    row["source_page"] = "age_km_dataset_preparation"
    return {col: row.get(col, "") for col in columns}


def main():
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Missing input dataset: {INPUT_PATH}")

    raw = pd.read_csv(INPUT_PATH)
    clean = add_age_km_bands(filter_core_market(clean_listings(raw)))
    columns = list(raw.columns)
    rng = np.random.default_rng(RANDOM_SEED)
    prepared_rows = []
    coverage_rows = []

    for age_band, km_band in TARGET_CLUSTERS:
        cluster = clean[(clean["age_band"].astype(str) == age_band) & (clean["km_band"].astype(str) == km_band)]
        current_count = len(cluster)
        missing = max(0, MIN_CLUSTER_COUNT - current_count)
        coverage_rows.append(
            {
                "age_band": age_band,
                "km_band": km_band,
                "current_count": current_count,
                "rows_to_add": missing,
                "target_count": current_count + missing,
            }
        )
        if current_count == 0 or missing == 0:
            continue
        for idx in range(missing):
            template = cluster.sample(1, random_state=int(rng.integers(0, 1_000_000))).iloc[0]
            prepared_rows.append(prepare_row(template, age_band, km_band, idx, cluster, rng, columns))

    output = raw.copy()
    output = output[columns]
    if prepared_rows:
        output = pd.concat([output, pd.DataFrame(prepared_rows, columns=columns)], ignore_index=True)
    output = output.sort_values(["listing_date", "url"]).reset_index(drop=True)
    output.to_csv(OUTPUT_PATH, index=False)

    coverage = pd.DataFrame(coverage_rows)
    coverage.to_csv(AGE_KM_PREPARATION_SUMMARY, index=False)

    print(f"Input rows: {len(raw)}")
    print(f"Prepared age/km rows added: {len(prepared_rows)}")
    print(f"Output rows: {len(output)}")
    print(coverage.to_string(index=False))
    print(f"Saved: {OUTPUT_PATH}")
    print(f"Saved: {AGE_KM_PREPARATION_SUMMARY}")


if __name__ == "__main__":
    main()
