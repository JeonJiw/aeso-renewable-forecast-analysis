# -*- coding: utf-8 -*-
"""
Run Full AESO Renewable Forecast Analysis Pipeline

Behavior:
- When this runner executes scripts, intermediate plots are HIDDEN (non-GUI backend),
  and ONLY the final dashboard plot from metrics is SHOWN.
- When you run each script directly yourself (not via this runner), plots will show
  unless you pass --no-show (your script's own flag).

Usage:
  python src/run_full_analysis.py [YEAR] [MONTH]
  python src/run_full_analysis.py [--year 2025] [--month 8]
"""

import subprocess
import os
import sys
import argparse
import calendar

# ------------------------------
# Setup
# ------------------------------
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
os.chdir(ROOT_DIR)

# Parse year/month (support both positional args and flags)
parser = argparse.ArgumentParser(description="Run full AESO renewable forecast analysis pipeline")
parser.add_argument("year_pos", nargs="?", type=int, default=None, metavar="YEAR", help="Target year (positional argument)")
parser.add_argument("month_pos", nargs="?", type=int, default=None, metavar="MONTH", help="Target month 1-12 (positional argument)")
parser.add_argument("--year", dest="year_flag", type=int, default=None, help="Target year (alternative to positional, overrides positional)")
parser.add_argument("--month", dest="month_flag", type=int, default=None, help="Target month 1-12 (alternative to positional, overrides positional)")

args = parser.parse_args()
# Priority: flags > positional > env > default
YEAR = args.year_flag if args.year_flag is not None else (args.year_pos if args.year_pos is not None else int(os.environ.get("YEAR", 2025)))
MONTH = args.month_flag if args.month_flag is not None else (args.month_pos if args.month_pos is not None else int(os.environ.get("MONTH", 8)))
if not (1 <= MONTH <= 12):
    print(f"❌ Invalid month: {MONTH}. Use 1..12")
    sys.exit(1)
MM = f"{MONTH:02d}"
MONTH_NAME = calendar.month_name[MONTH]

print(f"\n{'='*70}")
print(f"Running analysis for {MONTH_NAME} {YEAR}")
print(f"{'='*70}\n")

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
PIPE_ENV["YEAR"] = str(YEAR)
PIPE_ENV["MONTH"] = str(MONTH)

# FINAL_ENV → still pipeline mode, but ALLOW GUI for the very last plot
FINAL_ENV = dict(os.environ)
FINAL_ENV["RUN_PIPELINE"] = "1"
FINAL_ENV["YEAR"] = str(YEAR)
FINAL_ENV["MONTH"] = str(MONTH)
# ensure no forced headless backend for the final step
if "MPLBACKEND" in FINAL_ENV:
    del FINAL_ENV["MPLBACKEND"]

# ------------------------------
# Sequential Steps
# ------------------------------
steps = [
    # 1) Build CSV files (Solar_Data_{YEAR}_{MM}.csv, Wind_Data_{YEAR}_{MM}.csv)
    (f"Extract {MONTH_NAME} {YEAR} Data",
     f"python -m src.extract_month_data --year {YEAR} --month {MONTH}",
     PIPE_ENV),

    # 2) Graph 1: Forecast vs Actual (Merged CSV Saved) — No show
    ("Graph 1 — Forecast vs Actual (no show)",
     f"python src/graph1_forecast_vs_actual.py --year {YEAR} --month {MONTH} --no-show",
     PIPE_ENV),

    # 3) Graph 2: Total Supply & Rolling Variability — No show
    ("Graph 2 — Total Supply & Rolling Variability (no show)",
     f"python src/graph2_total_supply_variability.py --year {YEAR} --month {MONTH} --no-show",
     PIPE_ENV),

    # 4) Metrics Generation (hourly/daily CSV + Console Summary) — No plot
    ("Build Metrics (hourly & daily CSV)",
     f"python -m src.analysis_metrics --year {YEAR} --month {MONTH}",
     PIPE_ENV),

    # 5) Final Dashboard (Stability vs System Variability) — Show
    ("Final Dashboard — Stability vs System Variability (SHOW)",
     f"python src/plot_stability_comparison.py --year {YEAR} --month {MONTH} --show",
     FINAL_ENV),
]

for desc, cmd, env in steps:
    run_step(desc, cmd, env)

# ------------------------------
# Summary
# ------------------------------
print("\n🎉 All analysis steps completed successfully!\n")
print(f"Generated data for {MONTH_NAME} {YEAR}:")
print(f"  • data/Solar_Data_{YEAR}_{MM}.csv")
print(f"  • data/Wind_Data_{YEAR}_{MM}.csv")
print(f"  • data/merged_{YEAR}-{MM}.csv")
print(f"  • analysis/metrics_{YEAR}-{MM}_hourly.csv")
print(f"  • analysis/metrics_{YEAR}-{MM}_daily.csv")

print(f"\nGenerated figures for {MONTH_NAME} {YEAR}:")
print(f"  • figures/forecast_vs_actual_{YEAR}-{MM}.png            (hidden during pipeline)")
print(f"  • figures/graph2_total_supply_variability_{YEAR}-{MM}.png       (hidden during pipeline)")
print(f"  • figures/stability_comparison_{YEAR}-{MM}.png                  (SHOWN at the end)")
print(f"  • figures/stability_comparison_daily_{YEAR}-{MM}.png            (also saved)")

print("\n✅ Pipeline complete. Close the final figure window when finished.")