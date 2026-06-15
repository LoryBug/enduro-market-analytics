---
layout: default
title: Data Ingestion
nav_order: 2
---

# Data Ingestion Con Wayback Machine

## Panoramica

La parte di ingest costruisce la base dati grezza partendo da annunci pubblici di Moto.it, combinando snapshot storici recuperati da Internet Archive e pagine correnti del sito.

L'obiettivo è trasformare pagine HTML non strutturate in righe tabellari utilizzabili dalla pipeline analitica:

```text
Moto.it storico su Wayback Machine -> parsing HTML -> CSV raw -> consolidamento -> pipeline 01-07
```

La raccolta non è inclusa in `scripts/run_final_pipeline.py` perché dipende da rete, disponibilità delle pagine archiviate e tempi di risposta esterni. La pipeline finale lavora invece su uno snapshot raw consolidato e versionato, così l'analisi resta riproducibile.

---

## Script Di Raccolta

| Script | Ruolo | Output |
|---|---|---|
| `scripts/00_collect_wayback_moto.py` | Recupera snapshot storici via Internet Archive CDX API e Wayback Machine | `data/raw/enduro_listings_wayback.csv` |
| `scripts/00_collect_live_moto.py` | Recupera pagine correnti Moto.it riusando lo stesso parser | `data/raw/enduro_listings_wayback.csv` |
| `scripts/run_final_pipeline.py` | Esegue la pipeline analitica sul raw consolidato | `outputs/` e `data/processed/` |

Il file `data/raw/enduro_listings_wayback.csv` mantiene anche campi di tracciabilità come `url`, `archive_url` e `source_page`. Il file finale `data/raw/enduro_listings_raw.csv` contiene invece le colonne usate direttamente dalla pipeline analitica.

---

## Flusso Wayback Machine

Lo script `00_collect_wayback_moto.py` segue questi passaggi:

| Fase | Descrizione |
|---|---|
| Definizione target | Parte da pagine Moto.it dedicate a modelli e marchi enduro, incluse pagine successive. |
| Ricerca snapshot | Interroga `https://web.archive.org/cdx` filtrando HTML con status `200`. |
| Campionamento temporale | Seleziona snapshot distribuiti nel periodo configurato, evitando di prendere solo date vicine. |
| Download archivio | Scarica la pagina tramite URL Wayback `https://web.archive.org/web/{timestamp}/{original}`. |
| Parsing HTML | Estrae titolo, prezzo, anno, km, cilindrata, località, venditore e URL annuncio. |
| Normalizzazione | Converte date italiane, numeri, province, regioni, booleani e cilindrate inferite dal modello. |
| Deduplicazione | Usa la coppia `(snapshot_date, url)` per evitare duplicati nello stesso snapshot. |
| Salvataggio progressivo | Scrive il CSV dopo ogni target, riducendo il rischio di perdere raccolte parziali. |

La `snapshot_date` viene derivata dal timestamp Wayback e rappresenta il momento in cui il mercato è stato osservato. Questo rende possibile costruire una serie storica anche quando l'annuncio originale non è più online.

---

## Comandi Utili

Raccolta storica completa, con parametri di default:

```bash
python scripts/00_collect_wayback_moto.py
```

Raccolta limitata, utile per testare il parser senza scaricare tutto:

```bash
MAX_TARGETS=2 MAX_SNAPSHOTS=2 python scripts/00_collect_wayback_moto.py
```

Aggiunta di pagine correnti Moto.it:

```bash
python scripts/00_collect_live_moto.py
```

Esecuzione della pipeline analitica finale:

```bash
python scripts/run_final_pipeline.py
```

Variabili supportate dagli script di raccolta:

| Variabile | Uso |
|---|---|
| `FROM_YEAR` | Primo anno da cercare su Wayback Machine. |
| `TO_YEAR` | Ultimo anno da cercare su Wayback Machine. |
| `MAX_SNAPSHOTS` | Numero massimo di snapshot per pagina target. |
| `START_TARGET` | Indice del target da cui partire, utile per riprendere la raccolta. |
| `MAX_TARGETS` | Numero massimo di target da processare in una singola esecuzione. |
| `LIVE_SNAPSHOT_DATE` | Data da assegnare a una raccolta live. |

---

## Schema Dati Raw

La raccolta produce righe con queste colonne:

```csv
listing_date,snapshot_date,source,brand,model,year,km,engine_cc,price,region,province,seller_type,is_2stroke,condition_score,has_documents,url,archive_url,source_page
```

Le colonne principali hanno questo significato:

| Colonna | Significato |
|---|---|
| `listing_date` | Data dell'annuncio, quando disponibile nella pagina. |
| `snapshot_date` | Data dello snapshot Wayback o della raccolta live. |
| `source` | Origine della riga, ad esempio `moto.it-wayback` o `moto.it-live`. |
| `brand`, `model` | Marca e modello normalizzati in minuscolo. |
| `year`, `km`, `engine_cc`, `price` | Variabili quantitative estratte o inferite. |
| `region`, `province` | Localizzazione derivata dalla provincia, quando presente. |
| `archive_url` | URL della pagina archiviata usata come fonte. |
| `source_page` | Pagina Moto.it target da cui arriva lo snapshot. |

---

## Dall'Ingest Alla Pipeline

La pipeline finale usa `data/raw/enduro_listings_raw.csv`, uno snapshot consolidato costruito a partire dalla raccolta storica e corrente. Questo file rimuove i campi tecnici di tracciabilità e conserva le variabili necessarie all'analisi.

La separazione è intenzionale:

- la raccolta dimostra come i dati sono stati ottenuti e storicizzati;
- il raw consolidato garantisce che preprocessing, modelli e risultati siano rieseguibili;
- gli step `01-07` restano deterministici rispetto al dataset di input.

Pipeline completa dal punto di vista concettuale:

```text
01 ingest storico/live
02 consolidamento raw
03 preprocessing e feature engineering
04 aggregazione settimanale/mensile
05 forecast generale
06 segmentazione age/km
07 forecast cluster e raccomandazioni future
```

Nel repository, gli step analitici automatizzati sono quelli da `01_preprocess.py` a `07_future_buy_forecast.py`; gli script `00_*` documentano e permettono di rigenerare la fase di acquisizione quando necessario.
