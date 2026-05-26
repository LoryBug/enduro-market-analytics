# Selezione Del Mercato Basata Su Mediane

Questa analisi risponde alla richiesta del professore: trasformare gli annunci in mediane, selezionare un mercato coerente e ricavare un'interpretazione sensata.

## Mercato Principale Selezionato

Segmento principale: `core_modern_enduro_250_500`.

Regola di selezione:

```text
dataset completo; market_segment = modern; 250cc <= engine_cc <= 500cc; 1000 <= price <= 20000
```

Motivo: le enduro racing moderne 250-500cc sono il sotto-mercato più omogeneo. Le vintage/youngtimer e le 690/701 vengono tenute separate perché seguono dinamiche di prezzo diverse.

## Riepilogo Segmenti

| selected_segment           | definition                                                                                             |   months_with_data |   reliable_months_min10 | first_month   | last_month   |   total_listings |   median_of_monthly_medians | lowest_reliable_month   |   lowest_reliable_median | highest_reliable_month   |   highest_reliable_median |
|:---------------------------|:-------------------------------------------------------------------------------------------------------|-------------------:|------------------------:|:--------------|:-------------|-----------------:|----------------------------:|:------------------------|-------------------------:|:-------------------------|--------------------------:|
| core_modern_enduro_250_500 | Modern enduro listings, 250-500cc, excluding vintage/youngtimer rows.                                  |                 62 |                      29 | 2020-07-31    | 2026-05-31   |              894 |                      6800   | 2020-07-31              |                     5200 | 2025-12-31               |                      8675 |
| full_market                | All listings in the working dataset.                                                                   |                 72 |                      67 | 2020-06-30    | 2026-05-31   |             1891 |                      6225   | 2025-06-30              |                     3500 | 2025-04-30               |                     11000 |
| maxi_enduro_690_701        | KTM 690 / Husqvarna 701 style enduro listings, kept separate because prices differ from racing enduro. |                 34 |                      12 | 2020-06-30    | 2026-05-31   |              211 |                      7412.5 | 2026-04-30              |                     5900 | 2026-05-31               |                      8900 |
| vintage_epoca              | Vintage and youngtimer listings, kept separate because collector value distorts the market median.     |                 54 |                      13 | 2020-06-30    | 2026-05-31   |              598 |                      3400   | 2026-03-31              |                     2225 | 2024-05-31               |                      5150 |

## Mesi Recenti Affidabili Del Segmento Core

| period              |   listings_count |   median_price |   q25_price |   q75_price |   avg_age |
|:--------------------|-----------------:|---------------:|------------:|------------:|----------:|
| 2025-07-31 00:00:00 |               14 |           6850 |      4925   |      7490   |   5.28571 |
| 2025-08-31 00:00:00 |               44 |           6700 |      5287.5 |      9115   |   5.68182 |
| 2025-12-31 00:00:00 |               10 |           8675 |      6762.5 |      9662.5 |   4.8     |
| 2026-01-31 00:00:00 |               10 |           8150 |      7100   |      8575   |   3       |
| 2026-02-28 00:00:00 |               10 |           6800 |      6087.5 |      7222.5 |   3       |
| 2026-03-31 00:00:00 |               48 |           6425 |      5500   |      6992.5 |   6.27083 |
| 2026-04-30 00:00:00 |               45 |           6500 |      5700   |      7500   |   6.22222 |
| 2026-05-31 00:00:00 |              110 |           6000 |      4887.5 |      7400   |   5.2     |

## Interpretazione

Il progetto può mostrare il mercato completo come contesto, ma dovrebbe usare il segmento core come storia principale di forecasting. La mediana è preferibile alla media perché gli annunci includono outlier, moto d'epoca e cilindrate molto diverse.

Un mese viene considerato affidabile se contiene almeno 10 annunci nel segmento selezionato.