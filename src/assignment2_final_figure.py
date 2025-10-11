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
from zoneinfo import ZoneInfo  # py>=3.9

# ---------- Paths ----------
DATA_DIR = "data"
SOLAR_CSV = os.path.join(DATA_DIR, "Solar_Data_2025_Aug.csv")
WIND_CSV  = os.path.join(DATA_DIR, "Wind_Data_2025_Aug.csv")
CSD_CSV   = os.path.join(DATA_DIR, "CSD Generation (Hourly) - 2025-08.csv")

OUT_DIR = "figures"
os.makedirs(OUT_DIR, exist_ok=True)
OUT_PNG = os.path.join(OUT_DIR, "assignment2_final.png")

LOCAL_TZ = ZoneInfo("America/Edmonton")

# ---------- Helpers ----------
def pick_col(df, candidates):
    """Return the first existing column name (case-insensitive, strips spaces)."""
    cmap = {c.strip().lower(): c for c in df.columns}
    for cand in candidates:
        key = cand.strip().lower()
        if key in cmap:
            return cmap[key]
    return None

def add_DT(df):
    """
    Add unified datetime column 'DT' (keeps original time columns).
    Priority: 'dt' -> 'FORECAST_DATE_LOCAL' -> 'FORECAST_DATE_GMT'(UTC->local)
    """
    df = df.copy()
    df.columns = df.columns.str.strip()
    dt_src = pick_col(df, ["dt"])
    if dt_src:
        df["DT"] = pd.to_datetime(df[dt_src], errors="coerce")
    else:
        loc = pick_col(df, ["FORECAST_DATE_LOCAL"])
        gmt = pick_col(df, ["FORECAST_DATE_GMT"])
        if loc:
            df["DT"] = pd.to_datetime(df[loc].astype(str).str.strip(), errors="coerce")
        elif gmt:
            dt_utc = pd.to_datetime(df[gmt].astype(str).str.strip(), errors="coerce", utc=True)
            df["DT"] = dt_utc.dt.tz_convert(LOCAL_TZ).dt.tz_localize(None)
        else:
            raise KeyError("No time column (dt/FORECAST_DATE_LOCAL/FORECAST_DATE_GMT).")
    return df.dropna(subset=["DT"]).sort_values("DT")

def standardize_energy_cols(df, prefix):
    """
    Create standardized columns:
      <prefix>_FORECAST, <prefix>_ACTUAL, <prefix>_MIN, <prefix>_MAX
    Keeps originals; only adds renamed columns when found.
    Also coerces to numeric.
    """
    out = df.copy()
    # handle trailing spaces like 'ACTUAL '
    out.columns = out.columns.str.strip()
    mapping = {}
    for src, tgt in [
        ("OPT",    f"{prefix}_FORECAST"),
        ("ACTUAL", f"{prefix}_ACTUAL"),
        ("MIN",    f"{prefix}_MIN"),
        ("MAX",    f"{prefix}_MAX"),
    ]:
        c = pick_col(out, [src])
        if c:
            mapping[c] = tgt
    if mapping:
        out = out.rename(columns=mapping)
    for k in [f"{prefix}_FORECAST", f"{prefix}_ACTUAL", f"{prefix}_MIN", f"{prefix}_MAX"]:
        if k in out.columns:
            out[k] = pd.to_numeric(out[k], errors="coerce")
    return out

# ---------- Load Solar/Wind (already-August CSVs) ----------
solar_raw = pd.read_csv(SOLAR_CSV)
wind_raw  = pd.read_csv(WIND_CSV)

solar = add_DT(solar_raw)
wind  = add_DT(wind_raw)

# (Defensive) ensure August 2025 only
solar = solar[(solar["DT"].dt.year == 2025) & (solar["DT"].dt.month == 8)]
wind  = wind[(wind["DT"].dt.year == 2025) & (wind["DT"].dt.month == 8)]

solar_std = standardize_energy_cols(solar, "SOLAR")
wind_std  = standardize_energy_cols(wind,  "WIND")

solar_view = solar_std[["DT"] + [c for c in ["SOLAR_FORECAST","SOLAR_ACTUAL","SOLAR_MIN","SOLAR_MAX"] if c in solar_std.columns]]
wind_view  = wind_std[ ["DT"] + [c for c in ["WIND_FORECAST","WIND_ACTUAL","WIND_MIN","WIND_MAX"] if c in wind_std.columns]]

# Merge for subplot 1
merged = pd.merge_asof(
    left=solar_view.sort_values("DT"),
    right=wind_view.sort_values("DT"),
    on="DT",
    direction="nearest",
    tolerance=pd.Timedelta("30min"),
)

# ---------- Load CSD & compute total supply + rolling std ----------
csd = pd.read_csv(CSD_CSV)
csd.columns = csd.columns.str.strip()
# time column is "Date (MST)" per your sample
tcol = pick_col(csd, ["Date (MST)", "Date(MST)", "DATE (MST)"])
if not tcol:
    raise KeyError("Could not find 'Date (MST)' in CSD CSV.")
csd["DT"] = pd.to_datetime(csd[tcol], errors="coerce")
csd = csd.dropna(subset=["DT"])
csd = csd[(csd["DT"].dt.year == 2025) & (csd["DT"].dt.month == 8)]

# Sum Volume by hour across all assets
vcol = pick_col(csd, ["Volume"])
if not vcol:
    raise KeyError("Could not find 'Volume' column in CSD CSV.")
supply = csd.groupby("DT", as_index=False)[vcol].sum().rename(columns={vcol: "TOTAL_SUPPLY_MW"})
supply = supply.sort_values("DT")
supply["ROLLING_STD_24H"] = supply["TOTAL_SUPPLY_MW"].rolling(window=24).std()

# ---------- Colors ----------
SOLAR_FC, SOLAR_AC, SOLAR_FILL = "#d62728", "#ff7f7f", "#f28e8c"  # reds
WIND_FC,  WIND_AC,  WIND_FILL  = "#1f77b4", "#6baed6", "#9ecae1"  # blues

# ---------- Plot (2 subplots) ----------
fig = plt.figure(figsize=(13, 9))

# Subplot 1: Forecast vs Actual (Solar & Wind)
ax1 = fig.add_subplot(2,1,1)
ax1.set_title("Graph 1 — Forecast vs Actual (Aug 2025)")
ax1.set_xlabel("Time")
ax1.set_ylabel("MW")

# Wind
if {"WIND_MIN","WIND_MAX"}.issubset(merged.columns):
    ax1.fill_between(merged["DT"], merged["WIND_MIN"], merged["WIND_MAX"], color=WIND_FILL, alpha=0.28, label="Wind Forecast Range")
if "WIND_FORECAST" in merged.columns:
    ax1.plot(merged["DT"], merged["WIND_FORECAST"], color=WIND_FC, linewidth=2, label="Wind Forecast")
if "WIND_ACTUAL" in merged.columns:
    ax1.plot(merged["DT"], merged["WIND_ACTUAL"],   color=WIND_AC, linewidth=1.6, label="Wind Actual")

# Solar (markers help visibility)
if {"SOLAR_MIN","SOLAR_MAX"}.issubset(merged.columns):
    ax1.fill_between(merged["DT"], merged["SOLAR_MIN"], merged["SOLAR_MAX"], color=SOLAR_FILL, alpha=0.28, label="Solar Forecast Range")
if "SOLAR_FORECAST" in merged.columns:
    ax1.plot(merged["DT"], merged["SOLAR_FORECAST"], color=SOLAR_FC, linewidth=2, marker="o", markersize=2, label="Solar Forecast")
if "SOLAR_ACTUAL" in merged.columns:
    ax1.plot(merged["DT"], merged["SOLAR_ACTUAL"],   color=SOLAR_AC, linewidth=1.6, marker="o", markersize=2, label="Solar Actual")

ax1.legend(loc="upper right")
ax1.grid(alpha=0.3)

# Subplot 2: Total Supply + 24H Rolling Std
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

# Combined legend for subplot 2
ax2.legend(handles=[l1, l2], labels=["Total Supply (MW)", "24H Rolling Std"], loc="upper right")

fig.tight_layout()
fig.savefig(OUT_PNG, dpi=300, bbox_inches="tight")
plt.show()

print(f"[OK] Saved → {OUT_PNG}")