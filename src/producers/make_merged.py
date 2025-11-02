from __future__ import annotations
from pathlib import Path
import pandas as pd

def _ensure_parent(p: Path) -> Path:
    p.parent.mkdir(parents=True, exist_ok=True); return p

def _read_and_standardize(path: Path,
                          rename_map: dict[str,str] | None = None) -> pd.DataFrame:
    """
    Common preprocessing:
      - read
      - time column to timestamp and to_datetime
      - (optional) column name mapping
    """
    df = pd.read_csv(path, low_memory=False)
    # time column candidates
    cand = [c for c in ["DT","DateTime","Timestamp","timestamp","time","Time"] if c in df.columns]
    if not cand:
        raise ValueError(f"Could not find time column in {path}")
    dt_col = cand[0]
    df.rename(columns={dt_col: "timestamp"}, inplace=True)
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    if rename_map:
        df.rename(columns=rename_map, inplace=True)
    return df

def _asof_join(left: pd.DataFrame, right: pd.DataFrame, tol="30min") -> pd.DataFrame:
    """timestamp-based asof join (both sides must be sorted)."""
    l = left.sort_values("timestamp").copy()
    r = right.sort_values("timestamp").copy()
    out = pd.merge_asof(l, r, on="timestamp", tolerance=pd.Timedelta(tol))
    return out

def run(inputs: list[str], outputs: list[str]) -> None:
    """
    inputs : [Forecast.csv, Actual.csv]
    outputs: [merged_forecast_actual.csv]
    """
    if len(inputs) < 2 or len(outputs) < 1:
        raise ValueError("make_merged: inputs must be [Forecast.csv, Actual.csv] (2 required)")
    fc_path, ac_path = map(Path, inputs[:2])
    out_path = _ensure_parent(Path(outputs[0]))

    # read and standardize
    f = _read_and_standardize(fc_path, rename_map={"ForecastMW":"value","FuelType":"resource"})
    a = _read_and_standardize(ac_path, rename_map={"ActualMW":"value","FuelType":"resource"})

    # pivot by resource → wide
    # (e.g. each timestamp has a column for resource-specific value)
    f_piv = (f.pivot_table(index="timestamp", columns="resource", values="value", aggfunc="mean")
               .add_prefix("").add_suffix("_FORECAST"))
    a_piv = (a.pivot_table(index="timestamp", columns="resource", values="value", aggfunc="mean")
               .add_prefix("").add_suffix("_ACTUAL"))

    # time axis merge (outer)
    merged = pd.merge(f_piv, a_piv, left_index=True, right_index=True, how="outer")
    merged.reset_index(names="timestamp", inplace=True)
    merged.sort_values("timestamp", inplace=True)

    # further clean up common column names based on SOLAR/WIND (if present)
    col_map = {}
    for base in ["Solar","SOLAR","solar"]:
        if f"{base}_FORECAST" in merged.columns: col_map[f"{base}_FORECAST"] = "SOLAR_FORECAST"
        if f"{base}_ACTUAL"   in merged.columns: col_map[f"{base}_ACTUAL"]   = "SOLAR_ACTUAL"
    for base in ["Wind","WIND","wind"]:
        if f"{base}_FORECAST" in merged.columns: col_map[f"{base}_FORECAST"] = "WIND_FORECAST"
        if f"{base}_ACTUAL"   in merged.columns: col_map[f"{base}_ACTUAL"]   = "WIND_ACTUAL"
    if col_map:
        merged.rename(columns=col_map, inplace=True)

    merged.to_csv(out_path, index=False)