---
layout: default
title: Homepage
nav_order: 1
---

# Operational Analytics - Enduro Market Forecasting

## Obiettivo Del Progetto

Questo progetto analizza il mercato delle moto enduro usate con un obiettivo operativo: prevedere l'andamento del prezzo mediano e trasformare il forecast in indicazioni di acquisto.

Il problema non viene trattato come regressione sul prezzo del singolo annuncio. La scelta principale è costruire una serie temporale aggregata:

```text
annunci grezzi -> pulizia -> aggregazione mensile -> forecasting -> raccomandazione
```

Il progetto combina tre livelli di Operational Analytics:

- **Descriptive analytics**: pulizia, statistiche, mediane, segmentazione per età e chilometraggio.
- **Predictive analytics**: forecasting del prezzo mediano mensile del mercato e dei cluster principali.
- **Prescriptive analytics**: ranking dei mesi e dei cluster più convenienti per acquistare.

---

## Motivazione

Il mercato delle moto usate è rumoroso e molto eterogeneo. Due annunci possono avere prezzi diversi per motivi non sempre osservabili: stato reale del mezzo, manutenzione, accessori, trattabilità, urgenza del venditore e localizzazione.

Per questo il progetto usa:

- la **mediana** invece della media, per ridurre l'effetto degli outlier;
- la **frequenza mensile**, per avere osservazioni più stabili;
- un **segmento core** più omogeneo, invece del mercato completo;
- cluster **età/km**, per confrontare moto simili.

---

## Dati

Il dataset finale usato dalla pipeline è `data/raw/enduro_listings_raw.csv`.

| File | Contenuto | Righe |
|---|---|---:|
| `data/raw/enduro_listings_raw.csv` | Dataset di input della pipeline | 1930 |
| `data/processed/enduro_listings_clean.csv` | Dataset pulito finale | 1891 |

Copertura temporale:

| Serie | Osservazioni | Periodo |
|---|---:|---|
| Settimanale | 262 | 2020-06 -> 2026-05 |
| Mensile | 72 | 2020-06 -> 2026-05 |

Tutte le osservazioni vengono trattate nello stesso modo. L'analisi si concentra sulla trasformazione degli annunci in serie temporali aggregate e raccomandazioni operative.

---

## Approccio

La pipeline finale è eseguibile con:

```bash
python scripts/run_final_pipeline.py
```

La sequenza principale è:

| Step | Script | Output principale |
|---|---|---|
| Preprocessing | `01_preprocess.py` | serie settimanale e mensile |
| Forecast generale | `02_train_forecasting_models.py` | metriche e predizioni |
| Raccomandazioni base | `03_buying_period_recommendation.py` | mesi convenienti sul mercato generale |
| Segmentazione mediane | `04_median_selection_analysis.py` | segmento core e mediane |
| Analisi età/km | `05_age_km_market_insights.py` | matrici prezzo e conteggi |
| Forecast cluster | `06_cluster_forecasting.py` | metriche per cluster |
| Finestre future | `07_future_buy_forecast.py` | raccomandazioni future |

---

## Risultati Sintetici

Sul forecast generale il miglior modello è `random_forest`:

| Modello | MAE | RMSE | MAPE | R2 |
|---|---:|---:|---:|---:|
| Random Forest | 1402.22 | 1762.12 | 22.00% | 0.226 |
| Holt-Winters | 1713.03 | 2123.34 | 31.83% | -0.124 |
| Seasonal naive | 2311.07 | 2725.96 | 39.74% | -0.853 |
| MLP | 3306.16 | 4569.68 | 53.80% | -4.206 |

La parte più solida emerge però dai cluster età/km. Alcuni cluster hanno MAPE sotto il 10%, quindi sono più utili per produrre raccomandazioni operative.

La lettura stagionale mostra inoltre che la stagione motociclistica aprile-ottobre concentra più annunci, mentre i prezzi mediani osservati dipendono anche dal mix di moto disponibili nei diversi periodi dell'anno.

---

## Grafici Principali

![Distribuzione prezzi](img/01_price_distribution.png)

![Prezzo vs età](img/02_price_vs_age.png)

![Mediana mensile mercato](img/04_monthly_median_price.png)

![Segmento core](img/07_selected_core_monthly_median.png)

![Heatmap età km](img/08_age_km_price_heatmap.png)

![Forecast cluster](img/11_cluster_forecast_rmse.png)

![Finestre future](img/13_future_cluster_buy_windows.png)

---

## Contenuti

- [Preprocessing Dei Dati](preprocessing.md)
- [Forecasting Generale](forecasting.md)
- [Cluster Età/Km E Raccomandazioni](cluster_prescriptive.md)
- [Conclusioni E Confronto](conclusions.md)
- [Dataset Summary](dataset-summary.md)
