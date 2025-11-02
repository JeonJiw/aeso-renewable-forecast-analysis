"""
AESO    — specific adapter

Assumptions:
- original column names are:
  DateTime, ForecastMW, ActualMW, FuelType
- unit is MW
If needed, modify COLUMN_MAP_AESO or use generic_csv adapter.
"""
from __future__ import annotations
import pandas as pd

COLUMN_MAP_AESO = {
    "DateTime":  "timestamp",
    "ForecastMW":"forecast",
    "ActualMW":  "actual",
    "FuelType":  "resource",
}

def load(path_or_buf, **read_csv_kwargs) -> pd.DataFrame:
    """
    path_or_buf: str | file-like
    read_csv_kwargs: pandas.read_csv arguments (encoding, etc.)
    Returns: DataFrame with canonical schema (timestamp/forecast/actual/resource)
    """
    # AESO file is usually not large, so low_memory=False is stable
    df = pd.read_csv(path_or_buf, low_memory=False, **read_csv_kwargs)
    df = df.rename(columns=COLUMN_MAP_AESO)

    # minimum normalization: type correction
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    if "forecast" in df.columns:
        df["forecast"] = pd.to_numeric(df["forecast"], errors="coerce")
    if "actual" in df.columns:
        df["actual"]   = pd.to_numeric(df["actual"],   errors="coerce")
    if "resource" in df.columns:
        df["resource"] = df["resource"].astype("string")

    return df[["timestamp","forecast","actual","resource"]].copy()