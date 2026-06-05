"""Run the compact Enduro Market Analytics pipeline."""

import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
PIPELINE_STEPS = [
    "01_preprocess_descriptive.py",
    "02_forecasting.py",
    "03_recommendations.py",
]


def run_step(script_name):
    """Run one compact pipeline script."""
    print(f"\n==> {script_name}", flush=True)
    subprocess.run([sys.executable, script_name], cwd=PROJECT_ROOT, check=True)


def main():
    """Execute the compact pipeline in order."""
    for step in PIPELINE_STEPS:
        run_step(step)


if __name__ == "__main__":
    main()
