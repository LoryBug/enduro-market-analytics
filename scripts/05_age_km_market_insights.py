import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Rectangle

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.cluster_analysis import build_cluster_summary, build_count_matrix, build_monthly_cluster_series, build_price_matrix
from src.config import AGE_LABELS, KM_LABELS, MIN_CLUSTER_COUNT, OUTPUT_FIGURES, OUTPUT_TABLES, PROCESSED_LISTINGS
from src.segments import add_age_km_bands, filter_core_market


def load_core_market():
    df = pd.read_csv(PROCESSED_LISTINGS)
    df["observation_date"] = pd.to_datetime(df["observation_date"], errors="coerce")
    core = add_age_km_bands(filter_core_market(df))
    core = core.dropna(subset=["age_band", "km_band", "price"])
    return core


def build_buying_advice(summary):
    usable = summary[summary["listings_count"] > 0].copy()
    baseline = usable.loc[usable["listings_count"] >= MIN_CLUSTER_COUNT, "median_price"].median()
    if pd.isna(baseline):
        baseline = usable["median_price"].median()

    usable["discount_vs_core_baseline"] = baseline - usable["median_price"]
    usable["relative_discount_pct"] = usable["discount_vs_core_baseline"] / baseline * 100
    usable["value_label"] = np.select(
        [usable["relative_discount_pct"] >= 20, usable["relative_discount_pct"] >= 8, usable["relative_discount_pct"] <= -15],
        ["cheap", "fair", "expensive"],
        default="normal",
    )
    usable["buying_note"] = usable.apply(make_buying_note, axis=1)
    cols = [
        "age_band",
        "km_band",
        "listings_count",
        "coverage_status",
        "median_price",
        "q25_price",
        "q75_price",
        "discount_vs_core_baseline",
        "relative_discount_pct",
        "value_label",
        "buying_note",
    ]
    return usable[cols].sort_values(["value_label", "relative_discount_pct"], ascending=[True, False])


def make_buying_note(row):
    if row["coverage_status"] == "weak":
        return "Interpretare con cautela: cluster con pochi annunci."
    if row["value_label"] == "cheap":
        return "Cluster conveniente: prezzo mediano molto sotto la baseline del segmento core."
    if row["value_label"] == "fair":
        return "Buon compromesso: prezzo sotto baseline con copertura sufficiente."
    if row["value_label"] == "expensive":
        return "Cluster caro: adatto solo se si cerca moto molto recente o specifica."
    return "Cluster nella norma rispetto alla baseline del segmento core."


def save_heatmap(matrix, count_matrix, path):
    fig, ax = plt.subplots(figsize=(9, 5.8))
    values = matrix.to_numpy(dtype=float)
    masked = np.ma.masked_invalid(values)
    image = ax.imshow(masked, cmap="YlOrRd")
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
    if dimension == "age_band":
        labels = AGE_LABELS
        title = "Price distribution by age band"
        xlabel = "Age band (years)"
    else:
        labels = KM_LABELS
        title = "Price distribution by mileage band"
        xlabel = "Km band"

    data = [core.loc[core[dimension].astype(str) == label, "price"].dropna() for label in labels]
    non_empty = [(label, values) for label, values in zip(labels, data) if len(values) > 0]
    plot_labels = [item[0] for item in non_empty]
    plot_data = [item[1] for item in non_empty]

    fig, ax = plt.subplots(figsize=(8.8, 5.2))
    ax.boxplot(plot_data, labels=plot_labels, showfliers=False, patch_artist=True, medianprops={"color": "#111827", "linewidth": 2}, boxprops={"facecolor": "#fed7aa", "color": "#ea580c"}, whiskerprops={"color": "#ea580c"}, capprops={"color": "#ea580c"})
    counts = [len(values) for values in plot_data]
    medians = [values.median() for values in plot_data]
    for idx, (count, median) in enumerate(zip(counts, medians), start=1):
        ax.text(idx, median, f"n={count}\nEUR {median:,.0f}".replace(",", "."), ha="center", va="bottom", fontsize=8.5, color="#111827")
    ax.set_title(f"{title} - core modern enduro 250-500cc")
    plt.xlabel(xlabel)
    plt.ylabel("Asking price (EUR)")
    plt.grid(axis="y", alpha=0.25)
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()


def save_markdown(summary, buying_advice, matrix, count_matrix):
    strong = summary[summary["coverage_status"] == "strong"]
    weak = summary[summary["coverage_status"] == "weak"]
    empty = summary[summary["coverage_status"] == "empty"]
    top_advice = buying_advice.head(8)

    lines = [
        "# Age And Mileage Market Insights",
        "",
        "Analisi del segmento `core_modern_enduro_250_500` organizzato per fasce di eta e chilometraggio.",
        "",
        "## Fasce Usate",
        "",
        "- Km: `0-5k`, `5-10k`, `10-15k`, `15k+`",
        "- Eta: `0-2`, `3-5`, `6-10`, `11-20`, `20+` anni",
        "",
        "## Copertura Cluster",
        "",
        f"- Cluster forti, con almeno {MIN_CLUSTER_COUNT} annunci: **{len(strong)}**",
        f"- Cluster deboli, con 1-{MIN_CLUSTER_COUNT - 1} annunci: **{len(weak)}**",
        f"- Cluster vuoti: **{len(empty)}**",
        "",
        "## Matrice Prezzi MedianI",
        "",
        matrix.to_markdown(),
        "",
        "## Matrice Conteggi",
        "",
        count_matrix.to_markdown(),
        "",
        "## Consigli Di Acquisto Per Cluster",
        "",
        top_advice.to_markdown(index=False),
        "",
        "## Interpretazione",
        "",
        "L'eta spiega il prezzo in modo piu stabile dei km: le moto 0-2 anni hanno mediane piu alte, mentre le 11-20 anni costano molto meno. I km aiutano a distinguere ulteriormente i cluster, ma alcune fasce hanno pochi annunci e vanno rafforzate prima di usarle per forecasting dedicato.",
    ]
    (OUTPUT_TABLES / "age_km_market_insights.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    OUTPUT_TABLES.mkdir(parents=True, exist_ok=True)
    OUTPUT_FIGURES.mkdir(parents=True, exist_ok=True)

    core = load_core_market()
    summary = build_cluster_summary(core)
    price_matrix = build_price_matrix(summary)
    count_matrix = build_count_matrix(summary)
    buying_advice = build_buying_advice(summary)
    monthly_cluster_series = build_monthly_cluster_series(core)

    summary.to_csv(OUTPUT_TABLES / "age_km_cluster_summary.csv", index=False)
    price_matrix.to_csv(OUTPUT_TABLES / "age_km_price_matrix.csv")
    count_matrix.to_csv(OUTPUT_TABLES / "age_km_count_matrix.csv")
    buying_advice.to_csv(OUTPUT_TABLES / "buying_advice_by_age_km.csv", index=False)
    monthly_cluster_series.to_csv(OUTPUT_TABLES / "age_km_monthly_cluster_series.csv", index=False)

    save_heatmap(price_matrix, count_matrix, OUTPUT_FIGURES / "08_age_km_price_heatmap.png")
    save_band_boxplot(core, "age_band", OUTPUT_FIGURES / "09_price_by_age_band.png")
    save_band_boxplot(core, "km_band", OUTPUT_FIGURES / "10_price_by_km_band.png")
    save_markdown(summary, buying_advice, price_matrix, count_matrix)

    print(f"Core listings with age/km: {len(core)}")
    print(f"Saved: {OUTPUT_TABLES / 'age_km_cluster_summary.csv'}")
    print(f"Saved: {OUTPUT_TABLES / 'age_km_price_matrix.csv'}")
    print(f"Saved: {OUTPUT_TABLES / 'age_km_count_matrix.csv'}")
    print(f"Saved: {OUTPUT_TABLES / 'buying_advice_by_age_km.csv'}")
    print(f"Saved: {OUTPUT_TABLES / 'age_km_monthly_cluster_series.csv'}")
    print(f"Saved: {OUTPUT_TABLES / 'age_km_market_insights.md'}")
    print(f"Saved: {OUTPUT_FIGURES / '08_age_km_price_heatmap.png'}")
    print(f"Saved: {OUTPUT_FIGURES / '09_price_by_age_band.png'}")
    print(f"Saved: {OUTPUT_FIGURES / '10_price_by_km_band.png'}")


if __name__ == "__main__":
    main()
