---
layout: default
title: Preprocessing
nav_order: 2
---

# Preprocessing Dei Dati

## Panoramica

Il preprocessing trasforma gli annunci grezzi in dataset puliti e serie temporali aggregabili. Lo script principale è `scripts/01_preprocess.py`, che usa le funzioni definite in `src/preprocessing.py`.

L'obiettivo non è preparare un dataset per stimare il prezzo di una singola moto, ma costruire osservazioni temporali affidabili per il forecasting.

---

## 1. Struttura Del Dataset

Il dataset raw deve contenere almeno queste colonne:

```csv
listing_date,snapshot_date,source,brand,model,year,km,engine_cc,price,region,province,seller_type,is_2stroke,condition_score,has_documents
```

Tutte le righe del dataset vengono trattate come osservazioni del mercato e passano attraverso la stessa pipeline di pulizia, aggregazione e modellazione.

---

## 2. Pulizia E Standardizzazione

La funzione `clean_listings()` esegue queste operazioni:

| Operazione | Scopo |
|---|---|
| Parsing date | Converte `listing_date` in data utilizzabile |
| Conversione numerica | Converte `year`, `km`, `engine_cc`, `price`, `condition_score` |
| Normalizzazione testo | Standardizza brand, modello, fonte, regione, provincia, venditore |
| Parsing booleani | Converte `is_2stroke`, `has_documents` |
| Rimozione righe invalide | Elimina annunci senza data, anno o prezzo |
| Filtri base | Mantiene prezzi positivi e anni tra 1960 e 2026 |

Le righe non vengono filtrate in modo aggressivo perché il mercato dell'usato può contenere moto rare, d'epoca o restaurate. La robustezza viene ottenuta soprattutto tramite aggregazione e mediana.

---

## 3. Feature Derivate

Il preprocessing aggiunge variabili utili per analisi e modelli:

| Feature | Formula / Regola | Uso |
|---|---|---|
| `age` | `2026 - year` | Età della moto |
| `km_per_year` | `km / max(age, 1)` | Intensità di utilizzo |
| `price_per_cc` | `price / engine_cc` | Indicatore prezzo/cilindrata |
| `is_vintage` | `year < 1995` | Segmentazione storica |
| `is_youngtimer` | `1995 <= year < 2010` | Segmentazione storica |
| `market_segment` | vintage / youngtimer / modern | Analisi per segmento |
| `observation_date` | uguale a `listing_date` | Data di aggregazione |

---

## 4. Aggregazione Temporale

La pipeline genera due serie:

| Serie | File | Uso |
|---|---|---|
| Settimanale | `data/processed/weekly_market_series.csv` | Contesto e controllo |
| Mensile | `data/processed/monthly_market_series.csv` | Serie principale di forecasting |

La serie mensile è preferita perché il dataset non ha abbastanza densità per rendere stabile una previsione settimanale su tutti i segmenti.

Per ogni periodo vengono calcolate:

| Variabile | Significato |
|---|---|
| `avg_price` | prezzo medio |
| `median_price` | prezzo mediano, target principale |
| `listings_count` | numero annunci nel periodo |
| `avg_km` | chilometraggio medio |
| `avg_age` | età media |
| `vintage_share` | quota vintage |
| `youngtimer_share` | quota youngtimer |
| `two_stroke_share` | quota 2 tempi |
| `month`, `week_number` | feature temporali |

---

## 5. Perché La Mediana

Il target principale è `median_price`. La mediana è più adatta della media perché i prezzi degli annunci sono sbilanciati e possono includere outlier.

Esempio:

```text
Prezzi: 4000, 4500, 4700, 5000, 15000
Media: 6640
Mediana: 4700
```

Nel contesto dell'usato, la mediana rappresenta meglio il prezzo tipico osservato nel mercato.

---

## 6. Grafici Esplorativi

Il preprocessing produce i primi grafici descrittivi:

![Distribuzione prezzi](img/01_price_distribution.png)

La distribuzione evidenzia la presenza di prezzi molto diversi, confermando la scelta di usare mediane.

![Prezzo vs età](img/02_price_vs_age.png)

Il prezzo tende a diminuire con l'età, ma con molta dispersione: questo giustifica la segmentazione successiva.

![Mediana settimanale](img/03_weekly_median_price.png)

![Mediana mensile](img/04_monthly_median_price.png)

La serie mensile è più leggibile e stabile rispetto alla lettura settimanale.
