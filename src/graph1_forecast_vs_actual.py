# -*- coding: utf-8 -*-
"""
Plot Solar & Wind Forecast vs Actual — August 2025
- Keeps original time columns (dt / FORECAST_DATE_LOCAL / FORECAST_DATE_GMT).
- Adds a unified 'DT' column for merge/plot only (does NOT drop source time columns).
- Works with *_Aug.csv produced by the extractor.
- Color scheme: Solar=red family, Wind=blue family; ranges filled.
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from zoneinfo import ZoneInfo  # Python 3.9+

DATA_DIR = "data"
SOLAR_CSV = os.path.join(DATA_DIR, "Solar_Data_2025_Aug.csv")
WIND_CSV  = os.path.join(DATA_DIR, "Wind_Data_2025_Aug.csv")
OUT_PNG   = os.path.join("figures", "forecast_vs_actual_aug2025.png")
os.makedirs("figures", exist_ok=True)

LOCAL_TZ = ZoneInfo("America/Edmonton")

# ------------------------------
# Helpers
# ------------------------------
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
    Add a unified datetime column 'DT' without dropping source columns.
    Priority:
      1) 'dt' (already in *_Aug.csv)
      2) 'FORECAST_DATE_LOCAL'
      3) 'FORECAST_DATE_GMT' (convert UTC -> America/Edmonton, drop tz to naive)
    """
    # keep original columns; only ADD 'DT'
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
            raise KeyError("No time column found (dt / FORECAST_DATE_LOCAL / FORECAST_DATE_GMT).")

    df = df.dropna(subset=["DT"]).sort_values("DT")
    return df

def col(df, name):
    """Case-insensitive column getter; returns None if not present."""
    found = pick_col(df, [name])
    return found

def rename_energy(df, prefix):
    """
    Return a view with standardized energy columns:
      <prefix>_FORECAST, <prefix>_ACTUAL, <prefix>_MIN, <prefix>_MAX
    (Does not alter original columns; only adds/renames in a copy.)
    """
    out = df.copy()
    # Try common AESO names
    mapping = {}
    for src, tgt in [
        ("OPT",    f"{prefix}_FORECAST"),
        ("ACTUAL", f"{prefix}_ACTUAL"),
        ("MIN",    f"{prefix}_MIN"),
        ("MAX",    f"{prefix}_MAX"),
    ]:
        c = col(out, src)
        if c:
            mapping[c] = tgt
    if mapping:
        out = out.rename(columns=mapping)
    # ensure numeric
    for k in [f"{prefix}_FORECAST", f"{prefix}_ACTUAL", f"{prefix}_MIN", f"{prefix}_MAX"]:
        if k in out.columns:
            out[k] = pd.to_numeric(out[k], errors="coerce")
    return out

# ------------------------------
# Load
# ------------------------------
solar = pd.read_csv(SOLAR_CSV)
wind  = pd.read_csv(WIND_CSV)

# Trim header spaces like 'ACTUAL '
solar.columns = solar.columns.str.strip()
wind.columns  = wind.columns.str.strip()

# Add unified DT (keep original time columns)
solar = add_DT(solar)
wind  = add_DT(wind)

# Sanity: ensure August 2025
solar = solar[(solar["DT"].dt.year == 2025) & (solar["DT"].dt.month == 8)]
wind  = wind[(wind["DT"].dt.year == 2025) & (wind["DT"].dt.month == 8)]

# Standardize metric names (without deleting originals)
solar_std = rename_energy(solar, "SOLAR")
wind_std  = rename_energy(wind,  "WIND")

# Keep only needed columns for merge; but original columns are still in solar/wind if you need them
solar_view = solar_std[["DT"] + [c for c in ["SOLAR_FORECAST","SOLAR_ACTUAL","SOLAR_MIN","SOLAR_MAX"] if c in solar_std.columns]]
wind_view  = wind_std[ ["DT"] + [c for c in ["WIND_FORECAST","WIND_ACTUAL","WIND_MIN","WIND_MAX"] if c in wind_std.columns]]

# Merge by nearest timestamp (no aggregation)
merged = pd.merge_asof(
    left=solar_view.sort_values("DT"),
    right=wind_view.sort_values("DT"),
    on="DT",
    direction="nearest",
    tolerance=pd.Timedelta("30min"),
)

# ------------------------------
# Plot (single axis; Solar=reds, Wind=blues)
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

# Solar (use markers to help visibility when scale is small)
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

print(f"[OK] Saved → {OUT_PNG}")