import shutil
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import RAW_LISTINGS, RAW_PREPARED_LISTINGS

PIPELINE_STEPS = [
    "scripts/00_prepare_monthly_dataset.py",
    "scripts/00_prepare_age_km_dataset.py",
    "scripts/01_preprocess.py",
    "scripts/02_train_forecasting_models.py",
    "scripts/03_buying_period_recommendation.py",
    "scripts/04_median_selection_analysis.py",
    "scripts/05_age_km_market_insights.py",
    "scripts/06_cluster_forecasting.py",
    "scripts/07_future_buy_forecast.py",
]


def run_step(script_path):
    print(f"\n==> {script_path}", flush=True)
    subprocess.run([sys.executable, script_path], cwd=PROJECT_ROOT, check=True)


def main():
    for step in PIPELINE_STEPS[:2]:
        run_step(step)

    shutil.copyfile(RAW_PREPARED_LISTINGS, RAW_LISTINGS)
    print(
        f"\n==> copied {RAW_PREPARED_LISTINGS.relative_to(PROJECT_ROOT)} -> {RAW_LISTINGS.relative_to(PROJECT_ROOT)}",
        flush=True,
    )

    for step in PIPELINE_STEPS[2:]:
        run_step(step)


if __name__ == "__main__":
    main()
