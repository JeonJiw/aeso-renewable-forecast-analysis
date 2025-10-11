# -*- coding: utf-8 -*-
"""
Extract ALL hourly rows for August 2025 using Local time.
If FORECAST_DATE_LOCAL lacks hour:minute, rebuild local timestamps from FORECAST_DATE_GMT.
- Local TZ: America/Edmonton (MDT in August = UTC-6)
Run:
  source venv/bin/activate
  python src/extract_august_data.py
"""

import os
import pandas as pd
from zoneinfo import ZoneInfo  # py>=3.9

DATA_DIR = "data"
FILES = ["Solar_Data_2025.csv", "Wind_Data_2025.csv"]
LOCAL_COL = "FORECAST_DATE_LOCAL"
GMT_COL   = "FORECAST_DATE_GMT"
LOCAL_TZ  = ZoneInfo("America/Edmonton")  # Alberta (Calgary/Edmonton)

def build_local_dt(df: pd.DataFrame) -> pd.Series:
    """Return a Series of timezone-naive local datetimes with hour:minute preserved.
    Priority:
      1) Use LOCAL if it has varying hour/minute for the majority of rows.
      2) Else use GMT→local conversion (UTC→America/Edmonton).
    """
    cols = df.columns.str.strip()
    df.columns = cols
    has_local = LOCAL_COL in df.columns
    has_gmt   = GMT_COL in df.columns

    local = None
    if has_local:
        s = df[LOCAL_COL].astype(str).str.strip()
        local = pd.to_datetime(s, errors="coerce")
        # Heuristic: does LOCAL actually have time resolution?
        # If >80% of non-null rows have non-zero minute/hour variance, we trust LOCAL.
        if local.notna().sum() > 0:
            hour_var = local.dt.hour.nunique(dropna=True)
            minute_var = local.dt.minute.nunique(dropna=True)
            local_has_time = (hour_var > 1) or (minute_var > 1)
        else:
            local_has_time = False
    else:
        local_has_time = False

    if not local_has_time and has_gmt:
        # Rebuild from GMT
        s_gmt = pd.to_datetime(df[GMT_COL].astype(str).str.strip(), errors="coerce", utc=True)
        # Convert from UTC to local tz, then drop tz (naive local time)
        local = s_gmt.dt.tz_convert(LOCAL_TZ).dt.tz_localize(None)

    if local is None:
        raise ValueError("No usable datetime columns (LOCAL or GMT) found.")

    return local

def extract_august_local_all_rows(file_name: str):
    path = os.path.join(DATA_DIR, file_name)
    print(f"\n[INFO] Reading: {path}")

    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()  # trim headers like 'ACTUAL '
    # Build best local datetime (uses GMT if LOCAL lacks time)
    local_dt = build_local_dt(df)
    df = df.assign(dt=local_dt).dropna(subset=["dt"]).sort_values("dt")

    # Strict August 2025 filter (LOCAL time)
    aug = df[(df["dt"].dt.year == 2025) & (df["dt"].dt.month == 8)].copy()

    # Format for CSV without losing hour:minute
    aug["dt"] = aug["dt"].dt.strftime("%Y-%m-%d %H:%M")

    # Drop original time cols; keep unified 'dt' + other metrics
    keep_cols = ["dt"] + [c for c in df.columns if c not in {LOCAL_COL, GMT_COL, "dt"}]
    aug = aug[keep_cols]

    out_name = file_name.replace(".csv", "_Aug.csv")
    out_path = os.path.join(DATA_DIR, out_name)
    aug.to_csv(out_path, index=False)

    # sanity logs
    print(f"[OK] Saved → {out_path}")
    print(f"     Rows: {len(aug)}   First: {aug['dt'].iloc[0]}   Last: {aug['dt'].iloc[-1]}")
    per_day = pd.to_datetime(aug["dt"]).dt.date.value_counts().sort_index()
    print("     Per-day counts (first few):")
    print(per_day.head())

for f in FILES:
    extract_august_local_all_rows(f)