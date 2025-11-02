"""
Generic CSV adapter

Maps CSV from different providers to a standard schema.
- column_map: original -> canonical column name mapping dictionary
- datetime_*: time parsing/timezone handling
- units: unit conversion (kW <-> MW)
- resource_map: resource name standardization mapping

Canonical schema: timestamp(datetime64[ns/tz?]), forecast(float), actual(float), resource(str)
"""
from __future__ import annotations
import pandas as pd
from typing import Optional, Dict

def _parse_timestamp(
    series: pd.Series,
    fmt: Optional[str] = None,
    src_tz: Optional[str] = None,
    dst_tz: Optional[str] = None,
    nonexistent: str = "shift_forward",
    ambiguous: str = "infer",
) -> pd.Series:
    s = pd.to_datetime(series, format=fmt, errors="coerce")

    # tz handling: naive -> localize, aware -> convert
    # some pandas versions raise exception when accessing s.dt.tz, so use try
    tz = None
    try:
        tz = s.dt.tz
    except Exception:
        pass

    if tz is None and src_tz:
        s = s.dt.tz_localize(src_tz, nonexistent=nonexistent, ambiguous=ambiguous)
    if dst_tz:
        s = s.dt.tz_convert(dst_tz)
    return s

def _unit_multiplier(unit_in: str, unit_out: str) -> float:
    uin  = (unit_in  or "").lower()
    uout = (unit_out or "").lower()
    if uin == uout:
        return 1.0
    if uin == "kw" and uout == "mw":
        return 1/1000.0
    if uin == "mw" and uout == "kw":
        return 1000.0
    # add if needed (e.g. gw)
    return 1.0

def load(
    path_or_buf,
    *,
    column_map: Optional[Dict[str, str]] = None,
    # datetime options
    datetime_col: Optional[str] = None,
    datetime_format: Optional[str] = None,
    src_tz: Optional[str] = None,
    dst_tz: Optional[str] = None,
    nonexistent: str = "shift_forward",  # DST gap handling
    ambiguous: str = "infer",            # DST fold handling
    # unit options
    unit_in: str = "MW",
    unit_out: str = "MW",
    # resource name standardization
    resource_map: Optional[Dict[str, str]] = None,
    # pandas.read_csv arguments
    **read_csv_kwargs
) -> pd.DataFrame:
    """
Example: (e.g.)
    load("file.csv",
         column_map={"DT":"timestamp","Fcst":"forecast","Act":"actual","Fuel":"resource"},
         datetime_col="timestamp", datetime_format="%Y-%m-%d %H:%M",
         src_tz="UTC", dst_tz="America/Edmonton",
         unit_in="kW", unit_out="MW",
         resource_map={"Solar_PV":"Solar","Wind_On":"Wind"})
    """
    df = pd.read_csv(path_or_buf, low_memory=False, **read_csv_kwargs)

    # 1) column name standardization
    if column_map:
        df = df.rename(columns=column_map)

    # 2) timestamp parsing
    ts_col = datetime_col or ("timestamp" if "timestamp" in df.columns else None)
    if ts_col and ts_col in df.columns:
        df["timestamp"] = _parse_timestamp(
            df[ts_col],
            fmt=datetime_format,
            src_tz=src_tz,
            dst_tz=dst_tz,
            nonexistent=nonexistent,
            ambiguous=ambiguous,
        )

    # 3) numeric/unit correction
    mul = _unit_multiplier(unit_in, unit_out)
    if "forecast" in df.columns:
        df["forecast"] = pd.to_numeric(df["forecast"], errors="coerce") * mul
    if "actual" in df.columns:
        df["actual"]   = pd.to_numeric(df["actual"],   errors="coerce") * mul

    # 4) resource name standardization
    if resource_map and "resource" in df.columns:
        df["resource"] = df["resource"].map(lambda x: resource_map.get(x, x))

    # 5) type/column cleanup
    if "resource" in df.columns:
        df["resource"] = df["resource"].astype("string")

    needed = ["timestamp","forecast","actual","resource"]
    present = [c for c in needed if c in df.columns]
    if not present:
        # at least timestamp must be present for subsequent reshape step
        # here, return only the columns that are present
        return df.copy()

    return df[["timestamp","forecast","actual","resource"]].copy()