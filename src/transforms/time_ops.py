from __future__ import annotations
import pandas as pd

def filter_month(df: pd.DataFrame, month: int, *, tz_aware: bool = False) -> pd.DataFrame:
    s = df["timestamp"]
    if tz_aware and getattr(s.dt, "tz", None) is not None:
        m = s.dt.tz_convert(None).dt.month
    else:
        m = s.dt.month
    return df[m == month].copy()

def filter_between(
    df: pd.DataFrame, start: str | None = None, end: str | None = None
) -> pd.DataFrame:
    """
    Filter by period string (e.g. '2025-08-01', '2025-08-31 23:59').
    """
    s = pd.to_datetime(start) if start else None
    e = pd.to_datetime(end) if end else None
    out = df
    if s is not None:
        out = out[out["timestamp"] >= s]
    if e is not None:
        out = out[out["timestamp"] <= e]
    return out.copy()

def resample_by_resource(
    df: pd.DataFrame,
    *,
    freq: str = "1H",
    how: str = "mean",
) -> pd.DataFrame:
    """
    Resource-wise time resampling (mean/sum etc.). Assuming standard long format.
    """
    agg = {"forecast": how, "actual": how}
    out = (
        df.set_index("timestamp")
          .groupby("resource")
          .resample(freq)
          .agg(agg)
          .dropna(how="all")
          .reset_index()
          .sort_values("timestamp")
    )
    return out

def to_daily(df: pd.DataFrame, how: str = "mean") -> pd.DataFrame:
    """
    Daily aggregation by resource (default mean). Assuming standard long format.
    """
    g = (
        df.set_index("timestamp")
          .groupby("resource")
          .resample("1D")
          .agg({"forecast": how, "actual": how})
          .reset_index()
    )
    g["date"] = g["timestamp"].dt.date
    return g.drop(columns=["timestamp"]).sort_values("date")