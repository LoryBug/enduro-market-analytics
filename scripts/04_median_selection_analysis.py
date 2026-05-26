import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import (
    CORE_MONTHLY_SERIES,
    DATA_PROCESSED,
    OUTPUT_FIGURES,
    OUTPUT_TABLES,
    PROCESSED_LISTINGS,
)
from src.segments import filter_core_market


MIN_LISTINGS_PER_MONTH = 10


SEGMENTS = {
    "full_market": "All listings in the working dataset.",
    "core_modern_enduro_250_500": "Modern enduro listings, 250-500cc, excluding vintage/youngtimer rows.",
    "maxi_enduro_690_701": "KTM 690 / Husqvarna 701 style enduro listings, kept separate because prices differ from racing enduro.",
    "vintage_epoca": "Vintage and youngtimer listings, kept separate because collector value distorts the market median.",
}


def load_working_listings():
    df = pd.read_csv(PROCESSED_LISTINGS)
    df["observation_date"] = pd.to_datetime(df["observation_date"], errors="coerce")
    return df.copy()


def assign_selected_segments(df):
    full = df.copy()
    full["selected_segment"] = "full_market"

    core = filter_core_market(df)
    core["selected_segment"] = "core_modern_enduro_250_500"

    maxi = df[df["engine_cc"].isin([690, 701]) & df["price"].between(1000, 25000)].copy()
    maxi["selected_segment"] = "maxi_enduro_690_701"

    vintage = df[df["market_segment"].isin(["vintage", "youngtimer"]) & df["price"].between(500, 30000)].copy()
    vintage["selected_segment"] = "vintage_epoca"

    return pd.concat([full, core, maxi, vintage], ignore_index=True)


def monthly_medians(segmented):
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
    monthly["is_reliable_month"] = monthly["listings_count"] >= MIN_LISTINGS_PER_MONTH
    monthly["iqr_price"] = monthly["q75_price"] - monthly["q25_price"]
    return monthly


def segment_summary(monthly):
    rows = []
    for segment, group in monthly.groupby("selected_segment"):
        reliable = group[group["is_reliable_month"]]
        first = group["period"].min().date().isoformat()
        last = group["period"].max().date().isoformat()
        rows.append(
            {
                "selected_segment": segment,
                "definition": SEGMENTS[segment],
                "months_with_data": len(group),
                "reliable_months_min10": len(reliable),
                "first_month": first,
                "last_month": last,
                "total_listings": int(group["listings_count"].sum()),
                "median_of_monthly_medians": reliable["median_price"].median() if not reliable.empty else group["median_price"].median(),
                "lowest_reliable_month": reliable.loc[reliable["median_price"].idxmin(), "period"].date().isoformat() if not reliable.empty else "",
                "lowest_reliable_median": reliable["median_price"].min() if not reliable.empty else "",
                "highest_reliable_month": reliable.loc[reliable["median_price"].idxmax(), "period"].date().isoformat() if not reliable.empty else "",
                "highest_reliable_median": reliable["median_price"].max() if not reliable.empty else "",
            }
        )
    return pd.DataFrame(rows).sort_values("selected_segment")


def save_core_plot(monthly):
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
    OUTPUT_FIGURES.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUTPUT_FIGURES / "07_selected_core_monthly_median.png", dpi=150)
    plt.close()


def save_markdown_summary(summary, monthly):
    core = monthly[monthly["selected_segment"] == "core_modern_enduro_250_500"]
    core_reliable = core[core["is_reliable_month"]].copy()
    recent = core_reliable.sort_values("period").tail(8)

    lines = [
        "# Selezione Del Mercato Basata Su Mediane",
        "",
        "Questa analisi risponde alla richiesta del professore: trasformare gli annunci in mediane, selezionare un mercato coerente e ricavare un'interpretazione sensata.",
        "",
        "## Mercato Principale Selezionato",
        "",
        "Segmento principale: `core_modern_enduro_250_500`.",
        "",
        "Regola di selezione:",
        "",
        "```text",
        "dataset completo; market_segment = modern; 250cc <= engine_cc <= 500cc; 1000 <= price <= 20000",
        "```",
        "",
        "Motivo: le enduro racing moderne 250-500cc sono il sotto-mercato più omogeneo. Le vintage/youngtimer e le 690/701 vengono tenute separate perché seguono dinamiche di prezzo diverse.",
        "",
        "## Riepilogo Segmenti",
        "",
        summary.to_markdown(index=False),
        "",
        "## Mesi Recenti Affidabili Del Segmento Core",
        "",
        recent[["period", "listings_count", "median_price", "q25_price", "q75_price", "avg_age"]].to_markdown(index=False),
        "",
        "## Interpretazione",
        "",
        "Il progetto può mostrare il mercato completo come contesto, ma dovrebbe usare il segmento core come storia principale di forecasting. La mediana è preferibile alla media perché gli annunci includono outlier, moto d'epoca e cilindrate molto diverse.",
        "",
        f"Un mese viene considerato affidabile se contiene almeno {MIN_LISTINGS_PER_MONTH} annunci nel segmento selezionato.",
    ]
    (OUTPUT_TABLES / "median_selection_summary.md").write_text("\n".join(lines), encoding="utf-8")


def save_core_processed_series(monthly):
    core = monthly[monthly["selected_segment"] == "core_modern_enduro_250_500"].copy()
    core["week_number"] = core["period"].dt.isocalendar().week.astype(int)
    core["month"] = core["period"].dt.month
    cols = [
        "period",
        "median_price",
        "avg_price",
        "listings_count",
        "avg_km",
        "avg_age",
        "q25_price",
        "q75_price",
        "iqr_price",
        "is_reliable_month",
        "week_number",
        "month",
    ]
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    core[cols].to_csv(CORE_MONTHLY_SERIES, index=False)


def main():
    OUTPUT_TABLES.mkdir(parents=True, exist_ok=True)
    listings = load_working_listings()
    segmented = assign_selected_segments(listings)
    monthly = monthly_medians(segmented)
    summary = segment_summary(monthly)

    monthly.to_csv(OUTPUT_TABLES / "selected_monthly_medians.csv", index=False)
    summary.to_csv(OUTPUT_TABLES / "selected_market_summary.csv", index=False)
    save_core_processed_series(monthly)
    save_core_plot(monthly)
    save_markdown_summary(summary, monthly)

    print(f"Listings used: {len(listings)}")
    print(f"Selected core listings: {len(segmented[segmented['selected_segment'] == 'core_modern_enduro_250_500'])}")
    print(f"Saved: {OUTPUT_TABLES / 'selected_monthly_medians.csv'}")
    print(f"Saved: {OUTPUT_TABLES / 'selected_market_summary.csv'}")
    print(f"Saved: {CORE_MONTHLY_SERIES}")
    print(f"Saved: {OUTPUT_TABLES / 'median_selection_summary.md'}")
    print(f"Saved: {OUTPUT_FIGURES / '07_selected_core_monthly_median.png'}")


if __name__ == "__main__":
    main()
