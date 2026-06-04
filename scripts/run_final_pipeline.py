import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

PIPELINE_STEPS = [
    "scripts/01_preprocess.py",
    "scripts/02_train_forecasting_models.py",
    "scripts/03_buying_period_recommendation.py",
    "scripts/04_median_selection_analysis.py",
    "scripts/05_age_km_market_insights.py",
    "scripts/06_cluster_forecasting.py",
    "scripts/07_future_buy_forecast.py",
]


def run_step(script_path):
    """Run a single pipeline script via subprocess."""
    print(f"\n==> {script_path}", flush=True)
    subprocess.run([sys.executable, script_path], cwd=PROJECT_ROOT, check=True)


def main():
    """Execute all pipeline steps in order (01–07)."""
    for step in PIPELINE_STEPS:
        run_step(step)


if __name__ == "__main__":
    main()
