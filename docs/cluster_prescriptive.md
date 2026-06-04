---
layout: default
title: Cluster e Raccomandazioni
nav_order: 4
---

# Cluster Età/Km e Raccomandazioni

## Panoramica

La parte più operativa del progetto è la segmentazione del mercato core per età e chilometraggio. L'obiettivo è confrontare moto simili e trasformare il forecast in una raccomandazione di acquisto.

Gli script principali sono:

- `scripts/04_median_selection_analysis.py`
- `scripts/05_age_km_market_insights.py`
- `scripts/06_cluster_forecasting.py`
- `scripts/07_future_buy_forecast.py`

---

## 1. Selezione Del Segmento Core

Il mercato completo contiene moto moderne, youngtimer, vintage, cilindrate diverse e annunci anomali. Per ridurre rumore e outlier viene selezionato il segmento principale:

```text
market_segment = modern
250 <= engine_cc <= 500
1000 <= price <= 20000
```

Riepilogo segmenti:

| Segmento | Mesi | Mesi affidabili | Annunci | Mediana delle mediane |
|---|---:|---:|---:|---:|
| core_modern_enduro_250_500 | 62 | 29 | 894 | 6800 |
| full_market | 72 | 67 | 1891 | 6225 |
| maxi_enduro_690_701 | 34 | 12 | 211 | 7412.5 |
| vintage_epoca | 54 | 13 | 598 | 3400 |

![Segmento core](img/07_selected_core_monthly_median.png)

Il segmento core viene usato come storia principale perché evita di mescolare mercati diversi.

---

## 2. Cluster Età/Km

Le fasce usate sono:

| Dimensione | Fasce |
|---|---|
| Età | `0-2`, `3-5`, `6-10`, `11-20`, `20+` anni |
| Km | `0-5k`, `5-10k`, `10-15k`, `15k+` |

Copertura dei cluster principali:

| Età | Km | Annunci | Mediana | Copertura |
|---|---|---:|---:|---|
| 0-2 | 0-5k | 92 | 8550 | strong |
| 3-5 | 0-5k | 274 | 7200 | strong |
| 3-5 | 5-10k | 20 | 6175 | strong |
| 6-10 | 0-5k | 267 | 6200 | strong |
| 6-10 | 5-10k | 43 | 5900 | strong |
| 6-10 | 15k+ | 20 | 4800 | strong |
| 11-20 | 0-5k | 53 | 4100 | strong |
| 11-20 | 5-10k | 20 | 4400 | strong |

![Heatmap età km](img/08_age_km_price_heatmap.png)

La heatmap mostra che l'età organizza il prezzo in modo molto chiaro. Il chilometraggio raffina ulteriormente la lettura, ma alcuni cluster restano deboli.

---

## 3. Distribuzioni Per Fascia

![Prezzo per età](img/09_price_by_age_band.png)

Le moto più recenti hanno prezzi mediani più alti. Le fasce `11-20` anni diventano più convenienti, ma vanno interpretate considerando condizioni e disponibilità.

![Prezzo per km](img/10_price_by_km_band.png)

Il chilometraggio è utile, ma nel dataset disponibile è meno stabile dell'età perché molte enduro hanno km dichiarati bassi o poco confrontabili.

---

## 4. Buying Advice Descrittivo

Prima del forecast, il progetto produce consigli basati sulle mediane storiche del segmento core.

| Cluster | Annunci | Mediana | Valutazione | Nota |
|---|---:|---:|---|---|
| 11-20 / 0-5k | 53 | 4100 | cheap | prezzo molto sotto la baseline |
| 11-20 / 5-10k | 20 | 4400 | cheap | prezzo molto sotto la baseline |
| 6-10 / 15k+ | 20 | 4800 | cheap | conveniente ma con km alti |
| 6-10 / 5-10k | 43 | 5900 | normal | nella norma |
| 3-5 / 0-5k | 274 | 7200 | expensive | recente e costoso |
| 0-2 / 0-5k | 92 | 8550 | expensive | molto recente |

Questa è una lettura descrittiva: dice quali cluster sono storicamente più economici, non ancora quando comprare.

---

## 5. Forecast Per Cluster

Per evitare serie troppo corte, il forecast viene eseguito solo sui cluster con almeno 20 mesi osservati.

Risultati principali:

| Cluster | Best model | RMSE | MAPE | Raccomandazione corrente |
|---|---|---:|---:|---|
| 11-20 / 0-5k | Holt-Winters | 80.02 | 1.78% | neutral |
| 3-5 / 0-5k | Holt-Winters | 864.97 | 9.11% | neutral |
| 6-10 / 0-5k | Random Forest | 727.54 | 10.55% | good_buy |

![Accuratezza cluster](img/11_cluster_forecast_rmse.png)

![Buying score cluster](img/12_cluster_buy_score.png)

Il forecast per cluster è più interpretabile del forecast generale perché confronta moto più simili tra loro.

---

## 6. Finestre Future Di Acquisto

La raccomandazione futura confronta il prezzo previsto con la mediana storica dello stesso cluster:

```text
buy_score = historical_cluster_median - predicted_median_price
```

Se il valore è positivo, il mese previsto è potenzialmente più conveniente del normale per quel cluster.

Top raccomandazioni future:

| Periodo | Cluster | Prezzo previsto | Mediana storica | Buy score | Valutazione |
|---|---|---:|---:|---:|---|
| 2026-09 | 6-10 / 0-5k | 5804 | 6000 | 196 | good_buy |
| 2026-08 | 6-10 / 0-5k | 5819 | 6000 | 181 | good_buy |
| 2026-06 | 3-5 / 0-5k | 6925 | 7100 | 175 | neutral |
| 2026-07 | 3-5 / 0-5k | 6925 | 7100 | 175 | neutral |
| 2026-08 | 3-5 / 0-5k | 6925 | 7100 | 175 | neutral |

![Finestre future](img/13_future_cluster_buy_windows.png)

Questa è la parte prescrittiva: il forecast non resta una previsione numerica, ma diventa supporto alla decisione.
