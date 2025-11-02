from __future__ import annotations
import pandas as pd
import numpy as np

def add_total_supply(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate total forecast/actual by timestamp and add resource='Total' row.
    Assuming standard long format input → same format output.
    """
    base_cols = ["timestamp", "forecast", "actual"]
    base = df[base_cols + ["resource"]]

    total = (
        base.groupby("timestamp")[["forecast", "actual"]]
            .sum()
            .reset_index()
    )
    total["resource"] = "Total"
    out = pd.concat([base, total], ignore_index=True)
    return out[["timestamp", "forecast", "actual", "resource"]]

def rolling_variability(
    df_total: pd.DataFrame,
    *,
    window: str = "24H",
    target: str = "actual",
) -> pd.DataFrame:
    """
    Calculate rolling standard deviation for resource='Total' row (or single time series).
    Returns: ['timestamp','resource'(Total),'actual_std'] included.
    """
    d = df_total.copy()
    if "resource" in d.columns:
        d = d[d["resource"] == "Total"]
    s = d.set_index("timestamp")[target].rolling(window, min_periods=1).std()
    out = s.reset_index(name=f"{target}_std")
    out["resource"] = "Total"
    return out[["timestamp", "resource", f"{target}_std"]]

def add_errors(df: pd.DataFrame) -> pd.DataFrame:
    """
    Derive absolute error (AE), absolute percentage error (APE_%).
    """
    out = df.copy()
    out["AE"] = (out["forecast"] - out["actual"]).abs()
    denom = out["actual"].abs().clip(lower=1e-9)
    out["APE_%"] = out["AE"] / denom * 100.0
    return out

def in_range_flag(df: pd.DataFrame, band: float = 0.1) -> pd.DataFrame:
    """
    If actual is within ±band of forecast, return 1, otherwise 0.
    """
    out = df.copy()
    lower = out["forecast"] * (1 - band)
    upper = out["forecast"] * (1 + band)
    out["IN_RANGE"] = ((out["actual"] >= lower) & (out["actual"] <= upper)).astype(int)
    return out

def join_system_variability(
    df: pd.DataFrame, var_df: pd.DataFrame, *, on: str = "timestamp"
) -> pd.DataFrame:
    """
    Join system variability (rolling std etc.) time series to core df.
    var_df is recommended to be ['timestamp', '<target>_std'] format.
    """
    return df.merge(var_df, on=on, how="left")