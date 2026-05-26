# Age And Mileage Market Insights

Analisi del segmento `core_modern_enduro_250_500` organizzato per fasce di età e chilometraggio.

## Fasce Usate

- Km: `0-5k`, `5-10k`, `10-15k`, `15k+`
- Età: `0-2`, `3-5`, `6-10`, `11-20`, `20+` anni

## Copertura Cluster

- Cluster forti, con almeno 20 annunci: **8**
- Cluster deboli, con 1-19 annunci: **4**
- Cluster vuoti: **8**

## Matrice Prezzi Mediani

| age_band   |   0-5k |   5-10k |   10-15k |   15k+ |
|:-----------|-------:|--------:|---------:|-------:|
| 0-2        |   8550 |    7500 |      nan |    nan |
| 3-5        |   7200 |    6175 |      nan |    nan |
| 6-10       |   6200 |    5900 |     5800 |   4800 |
| 11-20      |   4100 |    4400 |     4300 |   5600 |
| 20+        |    nan |     nan |      nan |    nan |

## Matrice Conteggi

| age_band   |   0-5k |   5-10k |   10-15k |   15k+ |
|:-----------|-------:|--------:|---------:|-------:|
| 0-2        |     92 |       1 |        0 |      0 |
| 3-5        |    274 |      20 |        0 |      0 |
| 6-10       |    267 |      43 |        3 |     20 |
| 11-20      |     53 |      20 |       17 |     12 |
| 20+        |      0 |       0 |        0 |      0 |

## Consigli Di Acquisto Per Cluster

| age_band   | km_band   |   listings_count | coverage_status   |   median_price |   q25_price |   q75_price |   discount_vs_core_baseline |   relative_discount_pct | value_label   | buying_note                                                                    |
|:-----------|:----------|-----------------:|:------------------|---------------:|------------:|------------:|----------------------------:|------------------------:|:--------------|:-------------------------------------------------------------------------------|
| 11-20      | 0-5k      |               53 | strong            |           4100 |      3900   |     4750    |                      1937.5 |                32.0911  | cheap         | Cluster conveniente: prezzo mediano molto sotto la baseline del segmento core. |
| 11-20      | 10-15k    |               17 | weak              |           4300 |      4000   |     4700    |                      1737.5 |                28.7785  | cheap         | Interpretare con cautela: cluster con pochi annunci.                           |
| 11-20      | 5-10k     |               20 | strong            |           4400 |      4100   |     4650    |                      1637.5 |                27.1222  | cheap         | Cluster conveniente: prezzo mediano molto sotto la baseline del segmento core. |
| 6-10       | 15k+      |               20 | strong            |           4800 |      3937.5 |     5337.5  |                      1237.5 |                20.4969  | cheap         | Cluster conveniente: prezzo mediano molto sotto la baseline del segmento core. |
| 3-5        | 0-5k      |              274 | strong            |           7200 |      6300   |     8337.5  |                     -1162.5 |               -19.2547  | expensive     | Cluster caro: adatto solo se si cerca moto molto recente o specifica.          |
| 0-2        | 5-10k     |                1 | weak              |           7500 |      7500   |     7500    |                     -1462.5 |               -24.2236  | expensive     | Interpretare con cautela: cluster con pochi annunci.                           |
| 0-2        | 0-5k      |               92 | strong            |           8550 |      7500   |     9899.25 |                     -2512.5 |               -41.6149  | expensive     | Cluster caro: adatto solo se si cerca moto molto recente o specifica.          |
| 11-20      | 15k+      |               12 | weak              |           5600 |      4762.5 |     6412.25 |                       437.5 |                 7.24638 | normal        | Interpretare con cautela: cluster con pochi annunci.                           |

## Interpretazione

L'età spiega il prezzo in modo più stabile dei km: le moto 0-2 anni hanno mediane più alte, mentre le 11-20 anni costano molto meno. I km aiutano a distinguere ulteriormente i cluster, ma alcune fasce hanno pochi annunci e vanno rafforzate prima di usarle per forecasting dedicato.