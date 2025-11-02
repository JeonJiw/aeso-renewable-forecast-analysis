from __future__ import annotations
import pandas as pd
from typing import Iterable, Mapping

def wide_to_long_2resources(
    df: pd.DataFrame,
    *,
    ts_col: str = "timestamp",
    solar_fc: str = "SOLAR_FORECAST",
    solar_ac: str = "SOLAR_ACTUAL",
    wind_fc:  str = "WIND_FORECAST",
    wind_ac:  str = "WIND_ACTUAL",
) -> pd.DataFrame:
    """
    Convert wide format (SOLAR/WIND forecast/actual as columns) to standard long format (timestamp, forecast, actual, resource).
    """
    parts = []
    if {ts_col, solar_fc, solar_ac}.issubset(df.columns):
        a = df[[ts_col, solar_fc, solar_ac]].copy()
        a.columns = ["timestamp", "forecast", "actual"]
        a["resource"] = "Solar"
        parts.append(a)
    if {ts_col, wind_fc, wind_ac}.issubset(df.columns):
        b = df[[ts_col, wind_fc, wind_ac]].copy()
        b.columns = ["timestamp", "forecast", "actual"]
        b["resource"] = "Wind"
        parts.append(b)
    if not parts:
        raise ValueError("wide_to_long_2resources: could not find required columns for conversion")
    out = pd.concat(parts, ignore_index=True)
    out["timestamp"] = pd.to_datetime(out["timestamp"], errors="coerce")
    out = out.dropna(subset=["timestamp"]).sort_values("timestamp")
    return out[["timestamp", "forecast", "actual", "resource"]]

def melt_resources(
    df: pd.DataFrame,
    *,
    ts_col: str = "timestamp",
    value_cols: Mapping[str, str],
    resource_names: Mapping[str, str] | None = None,
) -> pd.DataFrame:
    """
    Convert arbitrary resource-specific columns to standard long format.
    value_cols: {"<original column>": "<role: forecast|actual>"} e.g. {"SolarFc":"forecast","SolarAc":"actual"}
    resource_names: {"SolarFc":"Solar","SolarAc":"Solar","WindFc":"Wind", ...}
    """
    if ts_col not in df.columns:
        raise ValueError("melt_resources: ts_col not found in dataframe")
    rows = []
    for col, role in value_cols.items():
        if col not in df.columns:
            continue
        res = resource_names[col] if resource_names else "Unknown"
        rows.append(
            df[[ts_col, col]]
            .rename(columns={ts_col: "timestamp", col: role})
            .assign(resource=res)
        )
    if not rows:
        raise ValueError("melt_resources: no columns to convert")
    # merge forecast/actual pairs by same timestamp+resource
    out = rows[0]
    for r in rows[1:]:
        out = out.merge(r, on=["timestamp", "resource"], how="outer")
    out["timestamp"] = pd.to_datetime(out["timestamp"], errors="coerce")
    return out.dropna(subset=["timestamp"]).sort_values("timestamp")