# -*- coding: utf-8 -*-
"""
Assignment 2 — Final Figure (2 Subplots, August 2025)
Top:  Forecast vs Actual (Solar=Red, Wind=Blue)
Bottom: Total Supply (left y) + 24H Rolling Std (right y)

Run:
  source venv/bin/activate
  python src/assignment2_final_figure.py
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from common import add_DT, standardize_energy, keep_august_2025

# ---------- Paths ----------
DATA_DIR = "data"
SOLAR_CSV = os.path.join(DATA_DIR, "Solar_Data_2025_Aug.csv")
WIND_CSV  = os.path.join(DATA_DIR, "Wind_Data_2025_Aug.csv")
CSD_CSV   = os.path.join(DATA_DIR, "CSD Generation (Hourly) - 2025-08.csv")

OUT_DIR = "figures"
os.makedirs(OUT_DIR, exist_ok=True)
OUT_PNG = os.path.join(OUT_DIR, "assignment2_final.png")

# ---------- Load Solar/Wind ----------
solar = pd.read_csv(SOLAR_CSV)
wind  = pd.read_csv(WIND_CSV)

solar = add_DT(solar)
wind  = add_DT(wind)

solar = keep_august_2025(solar)
wind  = keep_august_2025(wind)

solar_std = standardize_energy(solar, "SOLAR")
wind_std  = standardize_energy(wind,  "WIND")

solar_view = solar_std[["DT"] + [c for c in ["SOLAR_FORECAST","SOLAR_ACTUAL","SOLAR_MIN","SOLAR_MAX"] if c in solar_std.columns]]
wind_view  = wind_std[ ["DT"] + [c for c in ["WIND_FORECAST","WIND_ACTUAL","WIND_MIN","WIND_MAX"] if c in wind_std.columns]]

merged = pd.merge_asof(
    left=solar_view.sort_values("DT"),
    right=wind_view.sort_values("DT"),
    on="DT",
    direction="nearest",
    tolerance=pd.Timedelta("30min"),
)

# ---------- Load CSD (Total Supply) ----------
csd = pd.read_csv(CSD_CSV)
csd = add_DT(csd)
csd = keep_august_2025(csd)

supply = csd.groupby("DT", as_index=False)["Volume"].sum().rename(columns={"Volume": "TOTAL_SUPPLY_MW"})
supply["ROLLING_STD_24H"] = supply["TOTAL_SUPPLY_MW"].rolling(window=24).std()

# ---------- Colors ----------
SOLAR_FC, SOLAR_AC, SOLAR_FILL = "#d62728", "#ff7f7f", "#f28e8c"  # reds
WIND_FC,  WIND_AC,  WIND_FILL  = "#1f77b4", "#6baed6", "#9ecae1"  # blues

# ---------- Plot (2 subplots) ----------
fig = plt.figure(figsize=(13, 9))

# Subplot 1: Forecast vs Actual
ax1 = fig.add_subplot(2,1,1)
ax1.set_title("Graph 1 — Forecast vs Actual (Aug 2025)")
ax1.set_xlabel("Time")
ax1.set_ylabel("MW")

if {"WIND_MIN","WIND_MAX"}.issubset(merged.columns):
    ax1.fill_between(merged["DT"], merged["WIND_MIN"], merged["WIND_MAX"], color=WIND_FILL, alpha=0.28, label="Wind Forecast Range")
if "WIND_FORECAST" in merged.columns:
    ax1.plot(merged["DT"], merged["WIND_FORECAST"], color=WIND_FC, linewidth=2, label="Wind Forecast")
if "WIND_ACTUAL" in merged.columns:
    ax1.plot(merged["DT"], merged["WIND_ACTUAL"],   color=WIND_AC, linewidth=1.6, label="Wind Actual")

if {"SOLAR_MIN","SOLAR_MAX"}.issubset(merged.columns):
    ax1.fill_between(merged["DT"], merged["SOLAR_MIN"], merged["SOLAR_MAX"], color=SOLAR_FILL, alpha=0.28, label="Solar Forecast Range")
if "SOLAR_FORECAST" in merged.columns:
    ax1.plot(merged["DT"], merged["SOLAR_FORECAST"], color=SOLAR_FC, linewidth=2, marker="o", markersize=2, label="Solar Forecast")
if "SOLAR_ACTUAL" in merged.columns:
    ax1.plot(merged["DT"], merged["SOLAR_ACTUAL"],   color=SOLAR_AC, linewidth=1.6, marker="o", markersize=2, label="Solar Actual")

ax1.legend(loc="upper right")
ax1.grid(alpha=0.3)

# Subplot 2: Total Supply + Rolling Std
ax2 = fig.add_subplot(2,1,2)
ax2.set_title("Graph 2 — Total Supply & 24H Rolling Variability (Aug 2025)")
ax2.set_xlabel("Time")
ax2.set_ylabel("Total Supply (MW)", color="black")
l1, = ax2.plot(supply["DT"], supply["TOTAL_SUPPLY_MW"], color="black", linewidth=1.8, label="Total Supply (MW)")
ax2.tick_params(axis="y", labelcolor="black")
ax2.grid(alpha=0.3)

ax2b = ax2.twinx()
ax2b.set_ylabel("24H Rolling Std (MW)", color="orange")
l2, = ax2b.plot(supply["DT"], supply["ROLLING_STD_24H"], color="orange", linewidth=1.6, label="24H Rolling Std")
ax2b.tick_params(axis="y", labelcolor="orange")

ax2.legend(handles=[l1, l2], labels=["Total Supply (MW)", "24H Rolling Std"], loc="upper right")

fig.tight_layout()
fig.savefig(OUT_PNG, dpi=300, bbox_inches="tight")
plt.show()

print(f"[OK] Saved → {OUT_PNG}")