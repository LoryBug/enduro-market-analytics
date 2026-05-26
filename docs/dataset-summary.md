# Dataset Summary

## Dataset Corrente

Il dataset usato dalla pipeline finale e:

```text
data/raw/enduro_listings_raw.csv
```

## Origine Dati

| File | Contenuto | Righe |
|---|---|---:|
| `data/raw/enduro_listings_raw.csv` | Dataset di input della pipeline | 1930 |
| `data/processed/enduro_listings_clean.csv` | Dataset pulito finale | 1891 |

Fonti principali:

- snapshot storici Moto.it via Wayback Machine;
- pagine live Moto.it raccolte a maggio 2026.

Tutte le osservazioni vengono trattate nello stesso modo all'interno della pipeline.

## Copertura Temporale

| Serie | Osservazioni |
|---|---:|
| Settimanale | 312 |
| Mensile | 72 |

Periodo coperto:

```text
2020-06 -> 2026-05
```

## Segmento Principale

Il segmento principale per l'analisi operativa e:

```text
modern enduro 250-500cc
```

Regola:

```text
market_segment = modern
250 <= engine_cc <= 500
1000 <= price <= 20000
```

Output dedicati:

- `data/processed/core_modern_enduro_monthly_series.csv`
- `outputs/tables/selected_market_summary.csv`
- `outputs/tables/selected_monthly_medians.csv`

## Analisi Età/Km

Fasce usate:

- età: `0-2`, `3-5`, `6-10`, `11-20`, `20+` anni;
- km: `0-5k`, `5-10k`, `10-15k`, `15k+`.

Output principali:

- `outputs/tables/age_km_price_matrix.csv`
- `outputs/tables/age_km_count_matrix.csv`
- `outputs/tables/age_km_cluster_summary.csv`
- `outputs/tables/buying_advice_by_age_km.csv`
- `outputs/figures/08_age_km_price_heatmap.png`

## Forecasting

Modelli usati:

- `seasonal_naive` come baseline;
- `holt_winters` come metodo statistico;
- `random_forest` come metodo tree-based;
- `mlp` come metodo neural sul forecast generale.

Il forecast generale resta un benchmark. Il risultato operativo più utile e il forecast per cluster età/km, salvato in:

- `outputs/tables/cluster_forecast_metrics.csv`
- `outputs/tables/cluster_buying_scores.csv`
- `outputs/tables/future_cluster_buy_recommendations.csv`

## Dashboard

La dashboard finale e:

```text
report/index.html
```

Contiene panoramica dataset, mediane, segmentazione età/km, forecast per cluster e finestre future di acquisto.
