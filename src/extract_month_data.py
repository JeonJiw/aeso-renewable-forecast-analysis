# -*- coding: utf-8 -*-
"""
extract_month_data.py
Extract ALL hourly rows for a given year/month using Local time (per file),
mirroring the old August-only extractor but parameterized by --year/--month.
If FORECAST_DATE_LOCAL lacks hour:minute, rebuild local timestamps from FORECAST_DATE_GMT.
Local TZ: America/Edmonton.

Usage:
  python -m src.extract_month_data --year 2025 --month 9 \
    --solar data/Solar_Data_2025.csv --wind data/Wind_Data_2025.csv
# This script also writes data/merged_{YEAR}-{MM}.csv automatically.
"""

import os
import argparse
import calendar
import pandas as pd
from zoneinfo import ZoneInfo
from src.common import standardize_energy

DATA_DIR = "data"
LOCAL_COL = "FORECAST_DATE_LOCAL"
GMT_COL   = "FORECAST_DATE_GMT"
LOCAL_TZ  = ZoneInfo("America/Edmonton")


def ensure_dirs(path: str) -> None:
    """Create parent directory for a file path if missing."""
    d = path if os.path.splitext(path)[1] == "" else os.path.dirname(path)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)


def build_local_dt(df: pd.DataFrame) -> pd.Series:
    """Return timezone-naive local datetimes. Prefer LOCAL if it carries time; fallback to GMT->local."""
    df = df.copy()
    df.columns = df.columns.str.strip()
    has_local = LOCAL_COL in df.columns
    has_gmt   = GMT_COL in df.columns

    local = None
    local_has_time = False

    if has_local:
        s_local = pd.to_datetime(df[LOCAL_COL].astype(str).str.strip(), errors="coerce")
        if s_local.notna().any():
            hour_var = s_local.dt.hour.nunique(dropna=True)
            min_var  = s_local.dt.minute.nunique(dropna=True)
            local_has_time = (hour_var > 1) or (min_var > 1)
            local = s_local

    if (not local_has_time) and has_gmt:
        s_gmt = pd.to_datetime(df[GMT_COL].astype(str).str.strip(), errors="coerce", utc=True)
        local = s_gmt.dt.tz_convert(LOCAL_TZ).dt.tz_localize(None)

    if local is None:
        raise ValueError("No usable datetime columns (FORECAST_DATE_LOCAL or FORECAST_DATE_GMT).")

    return local


def extract_month_local_all_rows(input_path: str, year: int, month: int) -> None:
    print(f"\n[INFO] Reading: {input_path}")
    df = pd.read_csv(input_path)
    df.columns = df.columns.str.strip()

    # Build unified local dt and sort
    dt = build_local_dt(df)
    df = df.assign(dt=dt).dropna(subset=["dt"]).sort_values("dt")

    # Filter by year/month using local dt
    out = df[(df["dt"].dt.year == year) & (df["dt"].dt.month == month)].copy()

    # Keep unified 'dt' plus other columns (drop original time cols)
    out["dt"] = out["dt"].dt.strftime("%Y-%m-%d %H:%M")
    keep_cols = ["dt"] + [c for c in df.columns if c not in {LOCAL_COL, GMT_COL, "dt"}]
    out = out[keep_cols]

    # Output names (canonical only)
    base = os.path.basename(input_path)

    is_solar = "solar" in base.lower()
    is_wind  = "wind" in base.lower()
    out_name = None
    if is_solar:
        out_name = f"Solar_Data_{year}_{month:02d}.csv"
    elif is_wind:
        out_name = f"Wind_Data_{year}_{month:02d}.csv"
    else:
        # Fallback: keep a generic name using the canonical pattern
        stem = os.path.splitext(base)[0]
        out_name = f"{stem}_{year}_{month:02d}.csv"
    out_path = os.path.join(DATA_DIR, out_name)
    ensure_dirs(out_path)
    out.to_csv(out_path, index=False)
    print(f"[OK] Saved → {out_path}")

    # Quick stats
    print(f"     Rows: {len(out)}")
    if len(out) > 0:
        per_day = pd.to_datetime(out["dt"]).dt.date.value_counts().sort_index()
        print("     Per-day counts (head):")
        print(per_day.head())


def build_merged_from_month(year: int, month: int) -> str:
    """Create data/merged_{YEAR}-{MM}.csv by aligning Solar & Wind on local DT (±30 minutes).
    Assumes monthly extracts already exist as:
      - data/Solar_Data_{YEAR}_{MM}.csv
      - data/Wind_Data_{YEAR}_{MM}.csv
    Returns the merged CSV path.
    """
    MM = f"{month:02d}"
    solar_path = os.path.join(DATA_DIR, f"Solar_Data_{year}_{MM}.csv")
    wind_path  = os.path.join(DATA_DIR, f"Wind_Data_{year}_{MM}.csv")

    if not (os.path.isfile(solar_path) and os.path.isfile(wind_path)):
        raise FileNotFoundError(
            "Monthly solar/wind CSVs not found. Expected files:\n"
            f"  - {solar_path}\n  - {wind_path}\n"
            "Run the monthly extraction first in this script."
        )

    s = pd.read_csv(solar_path)
    w = pd.read_csv(wind_path)

    # Ensure unified datetime column 'DT' from extracted 'dt'
    s["DT"] = pd.to_datetime(s["dt"], errors="coerce")
    w["DT"] = pd.to_datetime(w["dt"], errors="coerce")
    s = s.dropna(subset=["DT"]).sort_values("DT").copy()
    w = w.dropna(subset=["DT"]).sort_values("DT").copy()

    # Standardize energy columns to SOLAR_* and WIND_*
    s = standardize_energy(s, prefix="SOLAR")
    w = standardize_energy(w, prefix="WIND")

    merged = pd.merge_asof(
        left=s.sort_values("DT"),
        right=w.sort_values("DT"),
        on="DT",
        direction="nearest",
        tolerance=pd.Timedelta("30min"),
    )

    out_path = os.path.join(DATA_DIR, f"merged_{year}-{MM}.csv")
    ensure_dirs(out_path)
    merged.to_csv(out_path, index=False)
    print(f"[OK] Saved merged → {out_path} (rows={len(merged)})")
    return out_path


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--year",  type=int, default=int(os.environ.get("YEAR", 2025)), help="Target year, e.g., 2025")
    ap.add_argument("--month", type=int, default=int(os.environ.get("MONTH", 8)),    help="Target month 1-12, e.g., 9")
    ap.add_argument("--solar", type=str, default=None, help="Path to yearly Solar CSV (e.g., data/Solar_Data_2025.csv)")
    ap.add_argument("--wind",  type=str, default=None, help="Path to yearly Wind CSV  (e.g., data/Wind_Data_2025.csv)")
    args = ap.parse_args()

    YEAR = args.year
    MONTH = args.month
    if not (1 <= MONTH <= 12):
        raise SystemExit(f"Invalid month: {MONTH}. Use 1..12")

    solar_in = args.solar if args.solar else os.path.join(DATA_DIR, f"Solar_Data_{YEAR}.csv")
    wind_in  = args.wind  if args.wind  else os.path.join(DATA_DIR, f"Wind_Data_{YEAR}.csv")

    # Debug print to confirm variables are passed correctly
    print(f"[ARGS] YEAR={YEAR}  MONTH={MONTH:02d}")
    print(f"[INPUT] SOLAR={solar_in}")
    print(f"[INPUT] WIND ={wind_in}")

    extract_month_local_all_rows(solar_in, YEAR, MONTH)
    extract_month_local_all_rows(wind_in,  YEAR, MONTH)
    build_merged_from_month(YEAR, MONTH)
