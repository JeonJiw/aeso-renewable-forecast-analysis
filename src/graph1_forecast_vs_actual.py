# -*- coding: utf-8 -*-
"""
Plot Solar & Wind Forecast vs Actual — August 2025
- Uses common utilities: add_DT(), keep_august_2025(), standardize_energy()
- Keeps original time columns (dt / FORECAST_DATE_LOCAL / FORECAST_DATE_GMT)
- Color scheme: Solar=red family, Wind=blue family; ranges filled.
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from common import add_DT, keep_august_2025, standardize_energy, parse_show_flag

DATA_DIR = "data"
SOLAR_CSV = os.path.join(DATA_DIR, "Solar_Data_2025_Aug.csv")
WIND_CSV  = os.path.join(DATA_DIR, "Wind_Data_2025_Aug.csv")
OUT_PNG   = os.path.join("figures", "forecast_vs_actual_aug2025.png")
os.makedirs("figures", exist_ok=True)

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

# Filter to August 2025 only
solar = keep_august_2025(solar)
wind  = keep_august_2025(wind)

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
MERGED_CSV = os.path.join(DATA_DIR, "merged_aug2025.csv")
merged.to_csv(MERGED_CSV, index=False)
print(f"[OK] Saved merged dataset → {MERGED_CSV}")

# ------------------------------
# Plot (Solar=reds, Wind=blues)
# ------------------------------
SOLAR_FC, SOLAR_AC, SOLAR_FILL = "#d62728", "#ff7f7f", "#f28e8c"
WIND_FC,  WIND_AC,  WIND_FILL  = "#1f77b4", "#6baed6", "#9ecae1"

plt.figure(figsize=(12, 6))
plt.title("Forecast vs Actual — August 2025 (Solar=Red, Wind=Blue)")
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
plt.show()

SHOW = parse_show_flag(default_show=True)  # standalone run = show by default

plt.savefig(OUT_PNG, dpi=300, bbox_inches="tight")
if SHOW:
    plt.show()
print(f"[OK] Saved → {OUT_PNG}")