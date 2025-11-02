from __future__ import annotations
from pathlib import Path
import os
import pandas as pd

DEFAULT_YEAR  = int(os.environ.get("AUG_YEAR",  2025))
DEFAULT_MONTH = int(os.environ.get("AUG_MONTH", 8))

def _ensure_parent(p: Path) -> Path:
    p.parent.mkdir(parents=True, exist_ok=True); return p

def _read_guess_dt(path: Path) -> pd.DataFrame:
    """Automatically detect common column names (DT, DateTime, timestamp) and parse as datetime."""
    df = pd.read_csv(path, low_memory=False)
    cand = [c for c in ["DT","DateTime","Timestamp","timestamp","time","Time"] if c in df.columns]
    if not cand:
        raise ValueError(f"Could not find time column in {path} (DT/DateTime/Timestamp required)")
    dt_col = cand[0]
    df.rename(columns={dt_col: "timestamp"}, inplace=True)
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    if df["timestamp"].isna().all():
        raise ValueError(f"Time column parsing failed for {path}")
    return df

def _filter_ym(df: pd.DataFrame, year: int, month: int) -> pd.DataFrame:
    m = (df["timestamp"].dt.year == year) & (df["timestamp"].dt.month == month)
    return df.loc[m].copy()

def run(inputs: list[str], outputs: list[str]) -> None:
    """
    inputs : [Solar_raw.csv, Wind_raw.csv]
    outputs: [Solar_Aug.csv, Wind_Aug.csv, merged_august.csv]  # 3rd is optional (no error if missing)

    Environment variables:
        AUG_YEAR (default 2025), AUG_MONTH (default 8)
    """
    if len(inputs) < 2:
        raise ValueError("make_august: inputs must be [Solar_raw, Wind_raw] (2 required)")
    solar_in, wind_in = map(Path, inputs[:2])

    # read & time parsing
    df_s = _read_guess_dt(solar_in)
    df_w = _read_guess_dt(wind_in)

    # August filter (default 2025-08)
    year, month = DEFAULT_YEAR, DEFAULT_MONTH
    df_s_aug = _filter_ym(df_s, year, month)
    df_w_aug = _filter_ym(df_w, year, month)

    # prepare output paths
    if len(outputs) < 2:
        raise ValueError("make_august: outputs must be [Solar_Aug, Wind_Aug, (optional merged)] (2 required)")
    solar_out = _ensure_parent(Path(outputs[0]))
    wind_out  = _ensure_parent(Path(outputs[1]))
    df_s_aug.to_csv(solar_out, index=False)
    df_w_aug.to_csv(wind_out,  index=False)

    # optional: save merged (simple time-based outer merge of two August datasets) (optional)
    if len(outputs) >= 3:
        merged_out = _ensure_parent(Path(outputs[2]))
        # prepare common keys
        left  = df_s_aug.rename(columns={"ForecastMW":"SOLAR_FORECAST","ActualMW":"SOLAR_ACTUAL"})
        right = df_w_aug.rename(columns={"ForecastMW":"WIND_FORECAST","ActualMW":"WIND_ACTUAL"})
        base_cols = ["timestamp","SOLAR_FORECAST","SOLAR_ACTUAL"]
        left  = left[ [c for c in base_cols if c in left.columns] + ([] if "resource" not in left else ["resource"]) ]
        base_cols = ["timestamp","WIND_FORECAST","WIND_ACTUAL"]
        right = right[ [c for c in base_cols if c in right.columns] + ([] if "resource" not in right else ["resource"]) ]

        merged = pd.merge(left, right, on="timestamp", how="outer", suffixes=("_S","_W"))
        merged.sort_values("timestamp", inplace=True)
        merged.to_csv(merged_out, index=False)