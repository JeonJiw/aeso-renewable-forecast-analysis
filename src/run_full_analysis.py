# -*- coding: utf-8 -*-
"""
Run Full AESO Renewable Forecast Analysis Pipeline

Behavior:
- When this runner executes scripts, intermediate plots are HIDDEN (non-GUI backend),
  and ONLY the final dashboard plot from metrics is SHOWN.
- When you run each script directly yourself (not via this runner), plots will show
  unless you pass --no-show (your script's own flag).

Usage:
  python src/run_full_analysis.py
"""

import subprocess
import os
import sys

# ------------------------------
# Setup
# ------------------------------
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
os.chdir(ROOT_DIR)

def run_step(description: str, command: str, env=None):
    """Run a shell command and display status with formatted output."""
    print("\n" + "="*70)
    print(f"▶ STEP: {description}")
    print("-"*70)
    try:
        subprocess.run(command, shell=True, check=True, env=env)
        print(f"✅ DONE: {description}")
    except subprocess.CalledProcessError as e:
        print(f"❌ FAILED: {description}")
        print(f"   Command: {command}")
        if e.returncode is not None:
            print(f"   Exit code: {e.returncode}")
        sys.exit(1)

# ------------------------------------------------
# ✅ Environment variables
# ------------------------------------------------
# PIPE_ENV → pipeline mode: hide intermediate plots, use non-GUI backend (Agg)
PIPE_ENV = dict(os.environ)
PIPE_ENV["RUN_PIPELINE"] = "1"
PIPE_ENV["MPLBACKEND"] = "Agg"  # force no-GUI

# FINAL_ENV → still pipeline mode, but ALLOW GUI for the very last plot
FINAL_ENV = dict(os.environ)
FINAL_ENV["RUN_PIPELINE"] = "1"
# ensure no forced headless backend for the final step
if "MPLBACKEND" in FINAL_ENV:
    del FINAL_ENV["MPLBACKEND"]

# ------------------------------
# Sequential Steps
# ------------------------------
steps = [
    # 1) Build CSV files (Solar_Data_2025_Aug.csv, Wind_Data_2025_Aug.csv)
    ("Extract August 2025 Data",
     "python src/extract_august_data.py",
     PIPE_ENV),

    # 2) Graph 1: Forecast vs Actual (Merged CSV Saved) — No show
    ("Graph 1 — Forecast vs Actual (no show)",
     "python src/graph1_forecast_vs_actual.py --no-show",
     PIPE_ENV),

    # 3) Graph 2: Total Supply & Rolling Variability — No show
    ("Graph 2 — Total Supply & Rolling Variability (no show)",
     "python src/graph2_total_supply_variability.py --no-show",
     PIPE_ENV),

    # 4) Metrics Generation (hourly/daily CSV + Console Summary) — No plot
    ("Build Metrics (hourly & daily CSV)",
     "python src/analysis_metrics_aug2025.py",
     PIPE_ENV),

    # 5) Final Dashboard (Stability vs System Variability) — Show
    ("Final Dashboard — Stability vs System Variability (SHOW)",
     "python src/plot_stability_comparison.py --show",
     FINAL_ENV),
]

for desc, cmd, env in steps:
    run_step(desc, cmd, env)

# ------------------------------
# Summary
# ------------------------------
print("\n🎉 All analysis steps completed successfully!\n")
print("Generated data:")
print("  • data/Solar_Data_2025_Aug.csv")
print("  • data/Wind_Data_2025_Aug.csv")
print("  • data/merged_aug2025.csv")
print("  • analysis/metrics_aug2025_hourly.csv")
print("  • analysis/metrics_aug2025_daily.csv")

print("\nGenerated figures:")
print("  • figures/forecast_vs_actual_aug2025.png            (hidden during pipeline)")
print("  • figures/graph2_total_supply_variability.png       (hidden during pipeline)")
print("  • figures/stability_comparison.png                  (SHOWN at the end)")
print("  • figures/stability_comparison_daily.png            (also saved)")

print("\n✅ Pipeline complete. Close the final figure window when finished.")