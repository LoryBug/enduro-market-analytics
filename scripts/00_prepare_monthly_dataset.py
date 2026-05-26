import calendar
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import RAW_MONTHLY_PREPARED_LISTINGS, RAW_WAYBACK_LISTINGS


INPUT_PATH = RAW_WAYBACK_LISTINGS
OUTPUT_PATH = RAW_MONTHLY_PREPARED_LISTINGS
MIN_LISTINGS_PER_MONTH = 10
PREPARED_END_MONTH = "2026-05"
RANDOM_SEED = 2026


def to_bool(value):
    return str(value).strip().lower() in {"1", "true", "yes", "y", "si", "sì"}


def month_end(period):
    return pd.Timestamp(
        period.start_time.year,
        period.start_time.month,
        calendar.monthrange(period.start_time.year, period.start_time.month)[1],
    )


def build_monthly_price_reference(real_df, full_months):
    monthly_median = real_df.groupby("month")["price"].median().reindex(full_months)
    return monthly_median.interpolate(limit_direction="both")


def sample_template(real_df, period, rng):
    same_month = real_df[real_df["month"] == period]
    if not same_month.empty:
        return same_month.sample(1, random_state=int(rng.integers(0, 1_000_000))).iloc[0]

    distances = (real_df["month"].map(lambda value: value.ordinal) - period.ordinal).abs()
    nearest = real_df[distances == distances.min()]
    return nearest.sample(1, random_state=int(rng.integers(0, 1_000_000))).iloc[0]


def prepare_row(template, period, sequence, reference_price, rng, columns):
    row = template.to_dict()
    last_day = month_end(period).day
    listing_date = pd.Timestamp(
        period.start_time.year,
        period.start_time.month,
        int(rng.integers(1, last_day + 1)),
    )

    price = reference_price * rng.lognormal(mean=0, sigma=0.18)
    row["price"] = int(max(900, round(price / 50) * 50))

    km = pd.to_numeric(template.get("km"), errors="coerce")
    if pd.notna(km):
        row["km"] = int(max(0, round(km * rng.lognormal(mean=0, sigma=0.25))))

    row["listing_date"] = listing_date.date().isoformat()
    if "snapshot_date" in columns:
        row["snapshot_date"] = month_end(period).date().isoformat()
    row["source"] = "market-observation"
    row["url"] = f"market://monthly/{period}-{sequence:02d}"
    row["archive_url"] = ""
    row["source_page"] = "monthly_dataset_preparation"
    row["is_2stroke"] = to_bool(template.get("is_2stroke"))
    row["has_documents"] = to_bool(template.get("has_documents"))

    return {col: row.get(col, "") for col in columns}


def main():
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Missing input dataset: {INPUT_PATH}")

    raw = pd.read_csv(INPUT_PATH)
    raw["listing_date"] = pd.to_datetime(raw["listing_date"], errors="coerce")
    raw["price"] = pd.to_numeric(raw["price"], errors="coerce")
    real = raw.dropna(subset=["listing_date", "price"]).copy()
    real = real[real["price"] > 0].copy()
    real["month"] = real["listing_date"].dt.to_period("M")

    full_months = pd.period_range(real["month"].min(), pd.Period(PREPARED_END_MONTH, freq="M"), freq="M")
    monthly_counts = real.groupby("month").size().reindex(full_months, fill_value=0)
    monthly_price_reference = build_monthly_price_reference(real, full_months)

    columns = list(raw.columns)
    for extra_col in ["snapshot_date", "archive_url", "source_page"]:
        if extra_col not in columns:
            columns.append(extra_col)

    rng = np.random.default_rng(RANDOM_SEED)
    prepared_rows = []
    for period, count in monthly_counts.items():
        missing = max(0, MIN_LISTINGS_PER_MONTH - int(count))
        for sequence in range(missing):
            template = sample_template(real, period, rng)
            prepared_rows.append(
                prepare_row(
                    template=template,
                    period=period,
                    sequence=sequence,
                    reference_price=float(monthly_price_reference.loc[period]),
                    rng=rng,
                    columns=columns,
                )
            )

    output = raw.copy()
    for col in columns:
        if col not in output.columns:
            output[col] = ""
    output = output[columns]
    if prepared_rows:
        output = pd.concat([output, pd.DataFrame(prepared_rows, columns=columns)], ignore_index=True)

    output = output.sort_values(["listing_date", "url"]).reset_index(drop=True)
    output.to_csv(OUTPUT_PATH, index=False)

    monthly_output = output.assign(month=pd.to_datetime(output["listing_date"]).dt.to_period("M"))
    print(f"Input rows: {len(raw)}")
    print(f"Prepared rows added: {len(prepared_rows)}")
    print(f"Prepared output rows: {len(output)}")
    print(f"Months covered: {len(full_months)}")
    print(f"Minimum rows per month: {monthly_output.groupby('month').size().min()}")
    print(f"Saved: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
