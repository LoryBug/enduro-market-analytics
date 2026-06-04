---
layout: default
title: Conclusioni
nav_order: 5
---

# Conclusioni e Confronto

## Panoramica

Il progetto costruisce una pipeline completa di Operational Analytics sul mercato delle enduro usate. Il contributo principale non è prevedere il prezzo esatto di una singola moto, ma trasformare annunci rumorosi in una serie temporale e poi in raccomandazioni operative.

La logica finale è:

```text
descriptive analytics -> predictive analytics -> prescriptive analytics
```

---

## 1. Riepilogo Performance Generale

| Modello | MAE | RMSE | MAPE | R2 | Lettura |
|---|---:|---:|---:|---:|---|
| Random Forest | 1402.22 | 1762.12 | 22.00% | 0.226 | migliore forecast generale |
| Holt-Winters | 1713.03 | 2123.34 | 31.83% | -0.124 | metodo statistico interpretabile |
| Seasonal naive | 2311.07 | 2725.96 | 39.74% | -0.853 | baseline battuta dai modelli migliori |
| MLP | 3306.16 | 4569.68 | 53.80% | -4.206 | non adatto come modello centrale |

![Forecast generale](img/05_forecast_comparison.png)

![RMSE generale](img/06_model_rmse_comparison.png)

Il risultato conferma che Random Forest sfrutta meglio le feature esplicative del mercato rispetto ai metodi puramente temporali.

---

## 2. Riepilogo Cluster

| Cluster | Best model | RMSE | MAPE | Interpretazione |
|---|---|---:|---:|---|
| 11-20 / 0-5k | Holt-Winters | 80.02 | 1.78% | serie molto stabile nel test |
| 3-5 / 0-5k | Holt-Winters | 864.97 | 9.11% | cluster ricco ma più variabile |
| 6-10 / 0-5k | Random Forest | 727.54 | 10.55% | buon compromesso operativo |

![Forecast cluster](img/11_cluster_forecast_rmse.png)

La segmentazione migliora l'utilità del forecast perché riduce il problema del mix degli annunci. Il mercato aggregato può cambiare prezzo anche solo perché cambia la composizione delle moto pubblicate.

---

## 3. Conclusione Operativa

La migliore lettura operativa attuale è:

| Periodo | Cluster | Prezzo previsto | Mediana storica | Buy score | Raccomandazione |
|---|---|---:|---:|---:|---|
| 2026-09 | 6-10 / 0-5k | 5804 | 6000 | 196 | good_buy |
| 2026-08 | 6-10 / 0-5k | 5819 | 6000 | 181 | good_buy |
| 2026-06 | 3-5 / 0-5k | 6925 | 7100 | 175 | neutral |
| 2026-07 | 3-5 / 0-5k | 6925 | 7100 | 175 | neutral |
| 2026-08 | 3-5 / 0-5k | 6925 | 7100 | 175 | neutral |

![Future buy windows](img/13_future_cluster_buy_windows.png)

La raccomandazione non significa che tutto il mercato sara economico. Significa che, per il cluster specifico `6-10 anni / 0-5k km`, il modello stima prezzi leggermente sotto la mediana storica del cluster.

---

## 4. Sintesi Metodologica

Il progetto è costruito come una pipeline completa di forecasting e supporto decisionale:

| Elemento | Scelta del progetto | Motivazione |
|---|---|---|
| Dominio | Annunci enduro usate | Mercato reale, eterogeneo e operativo |
| Target | Prezzo mediano futuro | Misura robusta rispetto agli outlier |
| Serie temporale | Annunci aggregati per mese | Frequenza più stabile dei dati settimanali |
| Metodo statistico | Holt-Winters | Modello interpretabile per trend e stagionalità |
| Metodo neural | MLP | Confronto non lineare sul benchmark generale |
| Metodo tree-based | Random Forest | Usa lag e variabili descrittive del mercato |
| Confronto metriche | MAE, RMSE, MAPE, R2 | Valutazione numerica completa |
| Output finale | Forecast + raccomandazione acquisto | Passaggio da predictive a prescriptive analytics |

La parte prescrittiva è centrale: il forecast viene tradotto in finestre di acquisto leggibili e motivate.

---

## 5. Limiti

| Limite | Impatto | Gestione |
|---|---|---|
| Dataset non enorme | Modelli complessi meno affidabili | Baseline e modelli robusti |
| Cluster con pochi dati | Forecast fragile su alcuni segmenti | Soglia minima di mesi osservati |
| Prezzi richiesti | Non sono prezzi finali di vendita | Interpretazione come mercato degli annunci |
| Variabili non osservate | Stato reale e manutenzione non pienamente catturati | Mediana e aggregazione temporale |

---

## 6. Conclusione Finale

Il punto forte del progetto è la coerenza tra obiettivo, dati e metodo. Invece di usare un modello complesso su dati rumorosi, la pipeline privilegia robustezza e interpretabilità:

```text
mediana mensile + segmento core + cluster età/km + forecast + buy score
```

Questa impostazione rende il progetto difendibile come Operational Analytics: prima descrive il mercato, poi prevede l'andamento dei cluster, infine produce una raccomandazione utilizzabile.
