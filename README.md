# Enduro Market Analytics

Progetto di Operational Analytics sul mercato delle moto enduro usate. L'obiettivo non è stimare il prezzo di un singolo annuncio, ma costruire serie temporali aggregate e trasformarle in indicazioni operative di acquisto.

Il progetto nasce da un problema pratico: stavo valutando l'acquisto di una moto da enduro usata e, nello stesso periodo, dovevo sviluppare un progetto per l'esame di Operational Analytics. Ho quindi trasformato una decisione personale in un caso analitico end-to-end: raccolta dati, preprocessing, forecasting e supporto alla scelta.

## Obiettivo

Il progetto combina tre livelli di analisi:

- **Descriptive analytics**: pulizia, aggregazione e studio del mercato per segmento, età e chilometraggio.
- **Predictive analytics**: forecasting del prezzo mediano mensile del mercato e dei cluster più omogenei.
- **Prescriptive analytics**: ranking dei periodi e dei cluster più convenienti per acquistare.

La parte più solida del progetto è la segmentazione `age/km`: il forecast generale resta un benchmark, mentre le raccomandazioni operative vengono costruite sui cluster più omogenei.

## Dataset

Il dataset raw consolidato usato dalla pipeline finale è:

```text
data/raw/enduro_listings_raw.csv
```

Il dataset raccoglie osservazioni storiche e correnti del mercato enduro in uno snapshot unico. Tutte le analisi derivano da questo file tramite preprocessing, aggregazione, forecasting e raccomandazione.

## Data Ingestion

La raccolta dati è separata dalla pipeline analitica per rendere il progetto riproducibile anche senza dipendere dalla rete o dalla disponibilità del sito sorgente.

- `scripts/00_collect_wayback_moto.py`: interroga la CDX API di Internet Archive, recupera snapshot storici di pagine Moto.it tramite Wayback Machine e normalizza gli annunci in `data/raw/enduro_listings_wayback.csv`.
- `scripts/00_collect_live_moto.py`: riusa lo stesso parser per acquisire pagine correnti di Moto.it e aggiungerle allo stesso file di raccolta.
- `data/raw/enduro_listings_raw.csv`: snapshot consolidato e stabile usato dagli step finali `01-07`.

In sintesi:

```text
Wayback Machine + Moto.it live -> raw collection -> raw consolidato -> preprocessing -> forecasting -> raccomandazioni
```

La raccolta via Wayback Machine permette di trasformare pagine archiviate nel tempo in osservazioni storiche del mercato, assegnando a ogni annuncio una `snapshot_date` coerente con la data dello snapshot.

## Pipeline

Esecuzione completa:

```bash
python scripts/run_final_pipeline.py
```

## Output Principali

- `outputs/tables/metrics.csv`: confronto modelli sul mercato generale.
- `outputs/tables/model_comparison_tests.csv`: confronto statistico pairwise degli errori dei modelli.
- `outputs/tables/seasonal_market_summary.csv`: confronto descrittivo tra stagioni e stagione motociclistica.
- `outputs/tables/cluster_forecast_metrics.csv`: metriche dei forecast per cluster età/km.
- `outputs/tables/future_cluster_buy_recommendations.csv`: finestre future di acquisto stimate.
- `outputs/tables/age_km_price_matrix.csv`: matrice prezzo mediano per età e km.
- `outputs/figures/*.png`: grafici generati dagli script.

## Risultato

Il forecast generale sul mercato completo è utile come baseline, ma l'errore resta alto perché la composizione degli annunci cambia nel tempo. Segmentando per età e chilometraggio si ottengono gruppi più omogenei, metriche migliori e consigli di acquisto più interpretabili.
