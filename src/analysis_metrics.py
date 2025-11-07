# -*- coding: utf-8 -*-
"""
Analysis metrics for a requested YEAR/MONTH (no plotting).

Inputs (for the same YEAR/MONTH):
  - data/merged_{YEAR}-{MM}.csv              (from Graph 1 step)
  - data/CSD Generation (Hourly) - {YEAR}-{MM}.csv  (AESO hourly CSD)

Outputs:
  - analysis/metrics_{YEAR}-{MM}_hourly.csv  (hour-level metrics)
  - analysis/metrics_{YEAR}-{MM}_daily.csv   (day-level summary)

Console:
  - Monthly summary (MAE, MAPE, Coverage, correlations)

Run examples:
  python -m src.analysis_metrics --year 2025 --month 9
  YEAR=2025 MONTH=9 python -m src.analysis_metrics
"""

import os
import argparse
import calendar
import numpy as np
import pandas as pd

from src.common import add_DT, ensure_dirs

# -------------------------------------------------------------------
# Parse YEAR/MONTH from flags or env
# -------------------------------------------------------------------
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

# -------------------------------------------------------------------
# Paths
# -------------------------------------------------------------------
DATA_DIR = "data"
AN_DIR   = "analysis"
ensure_dirs(AN_DIR)

MERGED_CSV = os.path.join(DATA_DIR, f"merged_{YEAR}-{MM}.csv")
CSD_CSV    = os.path.join(DATA_DIR, f"CSD Generation (Hourly) - {YEAR}-{MM}.csv")
OUT_HOURLY = os.path.join(AN_DIR,   f"metrics_{YEAR}-{MM}_hourly.csv")
OUT_DAILY  = os.path.join(AN_DIR,   f"metrics_{YEAR}-{MM}_daily.csv")

# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------
def _num(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce")

def safe_mean(s: pd.Series) -> float:
    s = pd.to_numeric(s, errors="coerce")
    return float(np.nanmean(s)) if s.notna().any() else float("nan")

def pct_from_flags01(s: pd.Series) -> float:
    s = pd.to_numeric(s, errors="coerce")
    return float(np.nanmean(s) * 100.0) if s.notna().any() else float("nan")

def safe_corr(x: pd.Series, y: pd.Series) -> float:
    x = pd.to_numeric(x, errors="coerce")
    y = pd.to_numeric(y, errors="coerce")
    tmp = pd.DataFrame({"x": x, "y": y}).dropna()
    if len(tmp) < 5:
        return float("nan")
    return float(tmp["x"].corr(tmp["y"]))

# -------------------------------------------------------------------
# 1) Load merged (Solar/Wind)
# -------------------------------------------------------------------
if not os.path.isfile(MERGED_CSV):
    raise FileNotFoundError(
        f"Missing '{MERGED_CSV}'. Build it in the Graph 1 step for {MONTH_NAME} {YEAR} first.")

merged = pd.read_csv(MERGED_CSV, parse_dates=["DT"])  # Graph1 already writes DT
merged.columns = merged.columns.str.strip()

# -------------------------------------------------------------------
# 2) Load CSD → TOTAL_SUPPLY_MW + ROLLING_STD_24H (same YEAR/MONTH)
# -------------------------------------------------------------------
if not os.path.isfile(CSD_CSV):
    raise FileNotFoundError(
        f"Missing '{CSD_CSV}'. Place the AESO CSD monthly file for {MONTH_NAME} {YEAR} in data/.")

csd = pd.read_csv(CSD_CSV)
csd = add_DT(csd)  # handles Date (MST/MDT/MPT) etc., normalizes to DT
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


# Compute per-source metrics
if {"SOLAR_FORECAST", "SOLAR_ACTUAL"}.issubset(df.columns):
    df["SOLAR_AE"]    = ae("SOLAR_FORECAST", "SOLAR_ACTUAL")
    df["SOLAR_APE_%"] = ape_pct("SOLAR_FORECAST", "SOLAR_ACTUAL")
if {"WIND_FORECAST", "WIND_ACTUAL"}.issubset(df.columns):
    df["WIND_AE"]     = ae("WIND_FORECAST",  "WIND_ACTUAL")
    df["WIND_APE_%"]  = ape_pct("WIND_FORECAST",  "WIND_ACTUAL")

if {"SOLAR_ACTUAL", "SOLAR_MIN", "SOLAR_MAX"}.issubset(df.columns):
    df["SOLAR_IN_RANGE"] = coverage01("SOLAR_ACTUAL", "SOLAR_MIN", "SOLAR_MAX")
if {"WIND_ACTUAL", "WIND_MIN", "WIND_MAX"}.issubset(df.columns):
    df["WIND_IN_RANGE"] = coverage01("WIND_ACTUAL",  "WIND_MIN",  "WIND_MAX")

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
ensure_dirs(OUT_HOURLY)
df[hourly_present].to_csv(OUT_HOURLY, index=False)
print(f"[OK] wrote hourly metrics → {OUT_HOURLY} (rows={len(df)})")

# -------------------------------------------------------------------
# 5) Daily summary
# -------------------------------------------------------------------
d = df.copy()
d["date"] = d["DT"].dt.date

agg_map = {}
if "SOLAR_AE" in d.columns:        agg_map["SOLAR_AE"]       = safe_mean
if "SOLAR_APE_%" in d.columns:     agg_map["SOLAR_APE_%"]    = safe_mean
if "SOLAR_IN_RANGE" in d.columns:  agg_map["SOLAR_IN_RANGE"] = pct_from_flags01
if "WIND_AE" in d.columns:         agg_map["WIND_AE"]        = safe_mean
if "WIND_APE_%" in d.columns:      agg_map["WIND_APE_%"]     = safe_mean
if "WIND_IN_RANGE" in d.columns:   agg_map["WIND_IN_RANGE"]  = pct_from_flags01
if "ROLLING_STD_24H" in d.columns: agg_map["ROLLING_STD_24H"] = safe_mean

if not agg_map:
    raise SystemExit("No metrics columns present to aggregate. Check inputs.")

daily = d.groupby("date").agg(agg_map).rename(columns={
    "SOLAR_AE":        "SOLAR_MAE",
    "SOLAR_APE_%":     "SOLAR_MAPE%",
    "SOLAR_IN_RANGE":  "SOLAR_Coverage%",
    "WIND_AE":         "WIND_MAE",
    "WIND_APE_%":      "WIND_MAPE%",
    "WIND_IN_RANGE":   "WIND_Coverage%",
    "ROLLING_STD_24H": "RollingStd24h",
}).reset_index()

ensure_dirs(OUT_DAILY)
daily.to_csv(OUT_DAILY, index=False)
print(f"[OK] wrote daily summary → {OUT_DAILY} (rows={len(daily)})")

# -------------------------------------------------------------------
# 6) Monthly summary (console)
# -------------------------------------------------------------------
SOLAR_MAE  = safe_mean(df["SOLAR_AE"])   if "SOLAR_AE"  in df.columns  else float("nan")
WIND_MAE   = safe_mean(df["WIND_AE"])    if "WIND_AE"   in df.columns  else float("nan")
SOLAR_MAPE = safe_mean(df["SOLAR_APE_%"]) if "SOLAR_APE_%" in df.columns else float("nan")
WIND_MAPE  = safe_mean(df["WIND_APE_%"])  if "WIND_APE_%"  in df.columns else float("nan")
SOLAR_COV  = pct_from_flags01(df["SOLAR_IN_RANGE"]) if "SOLAR_IN_RANGE" in df.columns else float("nan")
WIND_COV   = pct_from_flags01(df["WIND_IN_RANGE"])  if "WIND_IN_RANGE"  in df.columns else float("nan")

print(f"\n=== Monthly Summary ({MONTH_NAME} {YEAR}) ===")
if not np.isnan(SOLAR_MAE):
    print(f"Solar  MAE:  {SOLAR_MAE:.2f} MW   | MAPE: {SOLAR_MAPE:.2f}%   | Coverage: {SOLAR_COV:.0f}%")
if not np.isnan(WIND_MAE):
    print(f"Wind   MAE:  {WIND_MAE:.2f} MW   | MAPE: {WIND_MAPE:.2f}%   | Coverage: {WIND_COV:.0f}%")

# correlations if available
if "ROLLING_STD_24H" in df.columns:
    def print_if_corr_ok(name, x, y):
        val = safe_corr(x, y)
        if pd.notna(val):
            print(f"{name}: {val:.2f}")

    if "SOLAR_AE" in df.columns:
        print_if_corr_ok("Corr(Volatility, |Solar Error|)", df["ROLLING_STD_24H"], df["SOLAR_AE"])
    if "WIND_AE" in df.columns:
        print_if_corr_ok("Corr(Volatility, |Wind  Error|)", df["ROLLING_STD_24H"], df["WIND_AE"])

print("=====================================\n")