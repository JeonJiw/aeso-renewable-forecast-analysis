# -*- coding: utf-8 -*-
"""
Plot Solar & Wind Forecast vs Actual for a given year/month
- Uses common utilities: add_DT(), keep_month(), standardize_energy()
- Keeps original time columns (dt / FORECAST_DATE_LOCAL / FORECAST_DATE_GMT)
- Color scheme: Solar=red family, Wind=blue family; ranges filled.

Usage:
  python src/graph1_forecast_vs_actual.py [--year 2025] [--month 8] [--show|--no-show]
"""

import os
import argparse
import calendar
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from common import add_DT, keep_month, standardize_energy, parse_show_flag, ensure_dirs

# Parse year/month from args or env
parser = argparse.ArgumentParser(add_help=False)
parser.add_argument("--year", type=int, default=int(os.environ.get("YEAR", 2025)))
parser.add_argument("--month", type=int, default=int(os.environ.get("MONTH", 8)))
args, _ = parser.parse_known_args()
YEAR: int = args.year
MONTH: int = args.month
if not (1 <= MONTH <= 12):
    raise SystemExit(f"Invalid month: {MONTH}. Use 1..12")
MM = f"{MONTH:02d}"
MONTH_NAME = calendar.month_name[MONTH]

DATA_DIR = "data"
SOLAR_CSV = os.path.join(DATA_DIR, f"Solar_Data_{YEAR}_{MM}.csv")
WIND_CSV  = os.path.join(DATA_DIR, f"Wind_Data_{YEAR}_{MM}.csv")
OUT_PNG   = os.path.join("figures", f"forecast_vs_actual_{YEAR}-{MM}.png")
MERGED_CSV = os.path.join(DATA_DIR, f"merged_{YEAR}-{MM}.csv")

ensure_dirs(OUT_PNG) # ensure output directory exists

SHOW = parse_show_flag(default_show=False)
# ------------------------------
# Load & Preprocess
# ------------------------------
solar = pd.read_csv(SOLAR_CSV)
wind  = pd.read_csv(WIND_CSV)

# Trim header spaces
solar.columns = solar.columns.str.strip()
wind.columns  = wind.columns.str.strip()

# Add unified datetime column 
solar = add_DT(solar)
wind  = add_DT(wind)

# Filter to target year/month
solar = keep_month(solar, YEAR, MONTH)
wind  = keep_month(wind, YEAR, MONTH)

# Standardize column names (OPT→FORECAST, ACTUAL→ACTUAL, MIN/MAX)
solar_std = standardize_energy(solar, "SOLAR")
wind_std  = standardize_energy(wind, "WIND")

# Keep only relevant columns for merging
solar_view = solar_std[["DT"] + [c for c in ["SOLAR_FORECAST","SOLAR_ACTUAL","SOLAR_MIN","SOLAR_MAX"] if c in solar_std.columns]]
wind_view  = wind_std[ ["DT"] + [c for c in ["WIND_FORECAST","WIND_ACTUAL","WIND_MIN","WIND_MAX"] if c in wind_std.columns]]

# Merge by nearest timestamp (within ±30 min)
merged = pd.merge_asof(
    left=solar_view.sort_values("DT"),
    right=wind_view.sort_values("DT"),
    on="DT",
    direction="nearest",
    tolerance=pd.Timedelta("30min"),
)

# ------------------------------
# Save merged dataset for later analysis
# ------------------------------
ensure_dirs(MERGED_CSV)
merged.to_csv(MERGED_CSV, index=False)
print(f"[OK] Saved merged dataset → {MERGED_CSV}")

# ------------------------------
# Plot (Solar=reds, Wind=blues)
# ------------------------------
SOLAR_FC, SOLAR_AC, SOLAR_FILL = "#d62728", "#ff7f7f", "#f28e8c"
WIND_FC,  WIND_AC,  WIND_FILL  = "#1f77b4", "#6baed6", "#9ecae1"

plt.figure(figsize=(12, 6))
plt.title(f"Forecast vs Actual — {MONTH_NAME} {YEAR} (Solar=Red, Wind=Blue)")
plt.xlabel("Time"); plt.ylabel("MW")

# Wind
if {"WIND_MIN","WIND_MAX"}.issubset(merged.columns):
    plt.fill_between(merged["DT"], merged["WIND_MIN"], merged["WIND_MAX"], color=WIND_FILL, alpha=0.28, label="Wind Forecast Range")
if "WIND_FORECAST" in merged.columns:
    plt.plot(merged["DT"], merged["WIND_FORECAST"], color=WIND_FC, linewidth=2, label="Wind Forecast")
if "WIND_ACTUAL" in merged.columns:
    plt.plot(merged["DT"], merged["WIND_ACTUAL"],   color=WIND_AC, linewidth=1.6, label="Wind Actual")

# Solar
if {"SOLAR_MIN","SOLAR_MAX"}.issubset(merged.columns):
    plt.fill_between(merged["DT"], merged["SOLAR_MIN"], merged["SOLAR_MAX"], color=SOLAR_FILL, alpha=0.28, label="Solar Forecast Range")
if "SOLAR_FORECAST" in merged.columns:
    plt.plot(merged["DT"], merged["SOLAR_FORECAST"], color=SOLAR_FC, linewidth=2, marker="o", markersize=2, label="Solar Forecast")
if "SOLAR_ACTUAL" in merged.columns:
    plt.plot(merged["DT"], merged["SOLAR_ACTUAL"],   color=SOLAR_AC, linewidth=1.6, marker="o", markersize=2, label="Solar Actual")

plt.legend(loc="upper right")
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(OUT_PNG, dpi=300, bbox_inches="tight")
if SHOW:
    plt.show()
else:
    plt.close()
print(f"[OK] Saved → {OUT_PNG}")