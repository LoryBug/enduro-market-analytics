# Enduro Market Analytics - Compact Submission

This compact package contains the full reproducible pipeline in 8 files.

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
python run_pipeline.py
```

The pipeline creates runtime folders automatically:

- `data_processed/`: cleaned and derived datasets
- `outputs_tables/`: CSV results
- `outputs_figures/`: PNG figures

## Pipeline

1. `01_preprocess_descriptive.py`: cleans the raw dataset, builds market time series, selects the core segment, and creates age/km cluster insights.
2. `02_forecasting.py`: trains general market forecasting models and cluster forecasting models.
3. `03_recommendations.py`: builds general and future cluster-level buying recommendations.

Main input dataset: `enduro_listings_raw.csv`.
