# -*- coding: utf-8 -*-
"""
Analysis metrics for August 2025 (no plotting).

Inputs:
  - data/merged_aug2025.csv
  - data/CSD Generation (Hourly) - 2025-08.csv

Outputs:
  - analysis/metrics_aug2025_hourly.csv  (hour-level metrics)
  - analysis/metrics_aug2025_daily.csv   (day-level summary)

Console:
  - Monthly summary (MAE, MAPE, Coverage, correlations)
"""

import os
import numpy as np
import pandas as pd

# Optional: use add_DT from common.py if available (handles "Date (MST)/(MDT)/(MPT)" etc.)
try:
    from common import add_DT
except Exception:
    def add_DT(df: pd.DataFrame) -> pd.DataFrame:
        """Fallback: detect a datetime column and normalize to 'DT'."""
        df = df.copy()
        df.columns = df.columns.str.strip()
        for cand in ["DT", "Date (MST)", "Date (MDT)", "Date (MPT)", "Date"]:
            if cand in df.columns:
                df["DT"] = pd.to_datetime(df[cand], errors="coerce")
                break
        if "DT" not in df.columns:
            raise KeyError("No recognizable datetime column (DT/Date (MST)/MDT/MPT).")
        return df.dropna(subset=["DT"]).sort_values("DT")

# -------------------------------------------------------------------
# Paths
# -------------------------------------------------------------------
DATA_DIR = "data"
AN_DIR   = "analysis"
os.makedirs(AN_DIR, exist_ok=True)

MERGED_CSV = os.path.join(DATA_DIR, "merged_aug2025.csv")
CSD_CSV    = os.path.join(DATA_DIR, "CSD Generation (Hourly) - 2025-08.csv")
OUT_HOURLY = os.path.join(AN_DIR,   "metrics_aug2025_hourly.csv")
OUT_DAILY  = os.path.join(AN_DIR,   "metrics_aug2025_daily.csv")

# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------
def _num(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce")

def safe_mean(s: pd.Series) -> float:
    s = pd.to_numeric(s, errors="coerce")
    return float(np.nanmean(s)) if s.notna().any() else np.nan

def pct_from_flags01(s: pd.Series) -> float:
    s = pd.to_numeric(s, errors="coerce")
    return float(np.nanmean(s) * 100.0) if s.notna().any() else np.nan

def safe_corr(x: pd.Series, y: pd.Series) -> float:
    x = pd.to_numeric(x, errors="coerce")
    y = pd.to_numeric(y, errors="coerce")
    tmp = pd.DataFrame({"x": x, "y": y}).dropna()
    if len(tmp) < 5:
        return np.nan
    return float(tmp["x"].corr(tmp["y"]))

# -------------------------------------------------------------------
# 1) Load merged (Solar/Wind)
# -------------------------------------------------------------------
if not os.path.isfile(MERGED_CSV):
    raise FileNotFoundError(f"Missing '{MERGED_CSV}'. Build it in the Graph1 step first.")

merged = pd.read_csv(MERGED_CSV, parse_dates=["DT"])
merged.columns = merged.columns.str.strip()

# -------------------------------------------------------------------
# 2) Load CSD → TOTAL_SUPPLY_MW + ROLLING_STD_24H
# -------------------------------------------------------------------
csd = pd.read_csv(CSD_CSV)
csd = add_DT(csd)
csd = csd[(csd["DT"].dt.year == 2025) & (csd["DT"].dt.month == 8)]
csd_sum = csd.groupby("DT", as_index=False)["Volume"].sum().rename(columns={"Volume": "TOTAL_SUPPLY_MW"})
csd_sum = csd_sum.sort_values("DT")
csd_sum["ROLLING_STD_24H"] = csd_sum["TOTAL_SUPPLY_MW"].rolling(24).std()

# -------------------------------------------------------------------
# 3) Merge CSD into merged (nearest within ±30m)
# -------------------------------------------------------------------
df = pd.merge_asof(
    left=merged.sort_values("DT"),
    right=csd_sum.sort_values("DT"),
    on="DT",
    direction="nearest",
    tolerance=pd.Timedelta("30min"),
).sort_values("DT").reset_index(drop=True)

# -------------------------------------------------------------------
# 4) Compute hourly metrics
# -------------------------------------------------------------------
def ae(pred, act):
    if {pred, act}.issubset(df.columns):
        return (_num(df[pred]) - _num(df[act])).abs()
    return pd.Series(np.nan, index=df.index, dtype=float)

def ape_pct(pred, act):
    if {pred, act}.issubset(df.columns):
        f, a = _num(df[pred]), _num(df[act])
        out = pd.Series(np.nan, index=df.index, dtype=float)
        mask = a > 0
        out[mask] = (f[mask] - a[mask]).abs() / a[mask] * 100.0
        return out
    return pd.Series(np.nan, index=df.index, dtype=float)

def coverage01(act, lo, hi):
    if {act, lo, hi}.issubset(df.columns):
        a, l, h = _num(df[act]), _num(df[lo]), _num(df[hi])
        return ((a >= l) & (a <= h)).astype(float)
    return pd.Series(np.nan, index=df.index, dtype=float)

df["SOLAR_AE"]        = ae("SOLAR_FORECAST", "SOLAR_ACTUAL")
df["WIND_AE"]         = ae("WIND_FORECAST",  "WIND_ACTUAL")
df["SOLAR_APE_%"]     = ape_pct("SOLAR_FORECAST", "SOLAR_ACTUAL")
df["WIND_APE_%"]      = ape_pct("WIND_FORECAST",  "WIND_ACTUAL")
df["SOLAR_IN_RANGE"]  = coverage01("SOLAR_ACTUAL", "SOLAR_MIN", "SOLAR_MAX")
df["WIND_IN_RANGE"]   = coverage01("WIND_ACTUAL",  "WIND_MIN",  "WIND_MAX")

# Save hourly
hourly_cols = [
    "DT",
    "SOLAR_FORECAST","SOLAR_ACTUAL","SOLAR_MIN","SOLAR_MAX",
    "WIND_FORECAST","WIND_ACTUAL","WIND_MIN","WIND_MAX",
    "SOLAR_AE","SOLAR_APE_%","SOLAR_IN_RANGE",
    "WIND_AE","WIND_APE_%","WIND_IN_RANGE",
    "TOTAL_SUPPLY_MW","ROLLING_STD_24H",
]
hourly_present = [c for c in hourly_cols if c in df.columns]
df[hourly_present].to_csv(OUT_HOURLY, index=False)
print(f"[OK] wrote hourly metrics → {OUT_HOURLY} (rows={len(df)})")

# -------------------------------------------------------------------
# 5) Daily summary
# -------------------------------------------------------------------
d = df.copy()
d["date"] = d["DT"].dt.date

daily = d.groupby("date").agg({
    "SOLAR_AE":         safe_mean,
    "SOLAR_APE_%":      safe_mean,
    "SOLAR_IN_RANGE":   pct_from_flags01,
    "WIND_AE":          safe_mean,
    "WIND_APE_%":       safe_mean,
    "WIND_IN_RANGE":    pct_from_flags01,
    "ROLLING_STD_24H":  safe_mean,
}).rename(columns={
    "SOLAR_AE":        "SOLAR_MAE",
    "SOLAR_APE_%":     "SOLAR_MAPE%",
    "SOLAR_IN_RANGE":  "SOLAR_Coverage%",
    "WIND_AE":         "WIND_MAE",
    "WIND_APE_%":      "WIND_MAPE%",
    "WIND_IN_RANGE":   "WIND_Coverage%",
    "ROLLING_STD_24H": "RollingStd24h",
}).reset_index()

daily.to_csv(OUT_DAILY, index=False)
print(f"[OK] wrote daily summary → {OUT_DAILY} (rows={len(daily)})")

# -------------------------------------------------------------------
# 6) Monthly summary (console)
# -------------------------------------------------------------------
SOLAR_MAE  = safe_mean(df["SOLAR_AE"])
WIND_MAE   = safe_mean(df["WIND_AE"])
SOLAR_MAPE = safe_mean(df["SOLAR_APE_%"])
WIND_MAPE  = safe_mean(df["WIND_APE_%"])
SOLAR_COV  = pct_from_flags01(df["SOLAR_IN_RANGE"])
WIND_COV   = pct_from_flags01(df["WIND_IN_RANGE"])

def print_if_corr_ok(name, x, y):
    val = safe_corr(x, y)
    if pd.notna(val):
        print(f"{name}: {val:.2f}")

print("\n=== Monthly Summary (August 2025) ===")
print(f"Solar  MAE:  {SOLAR_MAE:.2f} MW   | MAPE: {SOLAR_MAPE:.2f}%   | Coverage: {SOLAR_COV:.0f}%")
print(f"Wind   MAE:  {WIND_MAE:.2f} MW   | MAPE: {WIND_MAPE:.2f}%   | Coverage: {WIND_COV:.0f}%")
print_if_corr_ok("Corr(Volatility, |Solar Error|)", df["ROLLING_STD_24H"], df["SOLAR_AE"])
print_if_corr_ok("Corr(Volatility, |Wind  Error|)", df["ROLLING_STD_24H"], df["WIND_AE"])
print("=====================================\n")