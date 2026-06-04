# Dataset Summary

## Dataset Corrente

Il dataset raw consolidato usato dalla pipeline finale è:

```text
data/raw/enduro_listings_raw.csv
```

## Origine Dati

| File | Contenuto | Righe |
|---|---|---:|
| `data/raw/enduro_listings_raw.csv` | Snapshot raw consolidato usato dalla pipeline | 1930 |
| `data/processed/enduro_listings_clean.csv` | Dataset pulito derivato localmente | 1891 |

Il dataset consolida osservazioni storiche e correnti del mercato enduro. Tutte le serie usate dalla pipeline vengono derivate localmente da questo file.

La colonna `snapshot_date` rappresenta il mese di osservazione del mercato ed e allineata alla fine del mese di `listing_date`.

## Versionamento

La repo segue una policy intermedia: restano versionati il raw consolidato, la documentazione, la dashboard e gli output finali in `outputs/`; restano invece fuori da Git i dati derivati rigenerabili.

File rigenerati localmente e ignorati:

- `data/processed/`

Per ricrearli e aggiornare gli output:

```bash
python scripts/run_final_pipeline.py
```

## Copertura Temporale

| Serie | Osservazioni |
|---|---:|
| Settimanale | 262 |
| Mensile | 72 |

Periodo coperto:

```text
2020-06 -> 2026-05
```

## Segmento Principale

Il segmento principale per l'analisi operativa è:

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

Il forecast generale resta un benchmark. Il risultato operativo più utile è il forecast per cluster età/km, salvato in:

- `outputs/tables/metrics.csv`
- `outputs/tables/model_comparison_tests.csv`
- `outputs/tables/cluster_forecast_metrics.csv`
- `outputs/tables/cluster_buying_scores.csv`
- `outputs/tables/future_cluster_buy_recommendations.csv`
