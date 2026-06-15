---
layout: default
title: Forecasting Generale
nav_order: 4
---

# Forecasting Generale

## Panoramica

Il forecasting generale usa la serie mensile del mercato come benchmark. Lo script principale è `scripts/02_train_forecasting_models.py`.

Questa parte serve a verificare se i modelli riescono a prevedere il `median_price` aggregato del mercato. Non è però la parte più forte del progetto, perché il mercato completo mescola moto molto diverse.

---

## 1. Target e Split Temporale

Target:

```text
median_price
```

La valutazione usa uno split cronologico: il modello viene addestrato sul passato e testato sui periodi successivi. Questo evita leakage temporale e simula lo scenario reale di forecasting.

Le feature lagged vengono costruite con `src/features.py`:

| Feature | Descrizione |
|---|---|
| `median_price_lag_1..4` | valori passati del target |
| `rolling_mean_4` | media mobile su 4 periodi |
| `rolling_std_4` | volatilita recente |
| `listings_count` | disponibilità annunci |
| `avg_km`, `avg_age` | composizione del mercato |
| `vintage_share`, `youngtimer_share` | mix storico |
| `two_stroke_share` | composizione tecnica |
| `month`, `week_number` | stagionalità calendario |

---

## 2. Modelli Confrontati

| Modello | Ruolo | Motivazione |
|---|---|---|
| `seasonal_naive` | Baseline | Verifica se modelli complessi aggiungono valore |
| `holt_winters` | Metodo statistico | Cattura livello, trend e stagionalità con complessità contenuta |
| `random_forest` | Tree-based ML | Usa lag e feature esplicative del mercato |
| `mlp` | Neural network | Confronto non lineare, non modello centrale |

La baseline è fondamentale: un modello avanzato ha senso solo se migliora una regola semplice.

---

## 3. Metriche

Le metriche usate sono:

| Metrica | Interpretazione |
|---|---|
| MAE | errore medio assoluto in euro |
| RMSE | errore quadratico medio, penalizza errori grandi |
| MAPE | errore percentuale medio |
| R2 | quota di variabilità spiegata rispetto alla media |

Risultati sul forecast generale:

| Modello | MAE | RMSE | MAPE | R2 |
|---|---:|---:|---:|---:|
| Random Forest | 1402.22 | 1762.12 | 22.00% | 0.226 |
| Holt-Winters | 1713.03 | 2123.34 | 31.83% | -0.124 |
| Seasonal naive | 2311.07 | 2725.96 | 39.74% | -0.853 |
| MLP | 3306.16 | 4569.68 | 53.80% | -4.206 |

Il miglior modello generale e `random_forest`, con MAPE pari a circa `22.00%`.

Oltre alle metriche aggregate, il progetto salva anche un confronto statistico pairwise degli errori assoluti in `outputs/tables/model_comparison_tests.csv`. Il test usato è un sign test esatto: per ogni coppia di modelli conta in quanti periodi un modello produce errore assoluto minore dell'altro e calcola un p-value sotto l'ipotesi che i due modelli abbiano la stessa probabilità di vincere sul periodo di test.

---

## 4. Grafici Di Confronto

![Forecast generale](img/05_forecast_comparison.png)

Il grafico confronta valori reali e previsioni dei modelli sul periodo di test.

![Confronto RMSE](img/06_model_rmse_comparison.png)

Random Forest risulta il modello migliore sul mercato generale, ma l'errore rimane significativo perché il prezzo mediano aggregato dipende anche dal mix degli annunci disponibili in ogni mese.

---

## 5. Interpretazione

Il forecast generale è utile come benchmark, ma non basta per prendere decisioni operative. Se in un mese aumentano le moto recenti, il prezzo mediano sale anche se il mercato non è realmente diventato più caro per ogni tipo di enduro.

Per questo il progetto sposta il focus su:

```text
mercato completo -> segmento core -> cluster età/km
```

La raccomandazione finale viene quindi costruita soprattutto sui cluster più omogenei.
