# Enduro Market Analytics

Progetto di Operational Analytics sul mercato delle moto enduro usate. L'obiettivo non è stimare il prezzo di un singolo annuncio, ma costruire serie temporali aggregate e trasformarle in indicazioni operative di acquisto.

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

Il dataset raccoglie osservazioni storiche e correnti del mercato enduro in uno snapshot unico. Tutte le osservazioni vengono trattate nello stesso modo durante preprocessing, aggregazione, forecasting e raccomandazione.

La repo mantiene versionati il dataset raw consolidato e gli output finali utili alla consegna. I file in `data/processed/` vengono rigenerati dalla pipeline e sono ignorati da Git.

## Pipeline

Esecuzione completa consigliata:

```bash
python scripts/run_final_pipeline.py
```

Collector opzionali, da lanciare solo per raccolte locali fuori dalla pipeline finale:

```bash
python scripts/00_collect_wayback_moto.py
python scripts/00_collect_live_moto.py
```

## Documentazione

La documentazione completa del progetto è nella cartella `docs/`:

- `docs/index.md`: panoramica, obiettivo, dati, approccio e grafici principali.
- `docs/preprocessing.md`: pulizia dati, feature engineering e aggregazione temporale.
- `docs/forecasting.md`: modelli, split temporale, metriche e risultati generali.
- `docs/cluster_prescriptive.md`: segmentazione età/km, forecast per cluster e raccomandazioni.
- `docs/conclusions.md`: confronto finale, limiti e conclusione operativa.

## Output Principali

- `outputs/tables/metrics.csv`: confronto modelli sul mercato generale.
- `outputs/tables/model_comparison_tests.csv`: confronto statistico pairwise degli errori dei modelli.
- `outputs/tables/cluster_forecast_metrics.csv`: metriche dei forecast per cluster età/km.
- `outputs/tables/future_cluster_buy_recommendations.csv`: finestre future di acquisto stimate.
- `outputs/tables/age_km_price_matrix.csv`: matrice prezzo mediano per età e km.
- `outputs/figures/*.png`: grafici generati dagli script.

## Risultato Sintetico

Il forecast generale sul mercato completo è utile come baseline, ma l'errore resta alto perché la composizione degli annunci cambia nel tempo. Segmentando per età e chilometraggio si ottengono gruppi più omogenei, metriche migliori e consigli di acquisto più interpretabili.

Esempio di output operativo:

```text
Settembre 2026 emerge come possibile finestra conveniente per il cluster 3-5 anni / 0-5k km, perché il prezzo previsto è sotto la mediana storica del cluster.
```

## Struttura

```text
data/raw/        dataset raw consolidato
data/processed/  dataset derivati rigenerati localmente
scripts/         pipeline eseguibile
src/             funzioni riutilizzabili per preprocessing, modelli, metriche e plot
outputs/         tabelle e figure finali versionate
docs/            note metodologiche
```
