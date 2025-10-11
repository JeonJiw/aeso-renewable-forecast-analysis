import pandas as pd
from zoneinfo import ZoneInfo

LOCAL_TZ = ZoneInfo("America/Edmonton")

def pick_col(df, candidates):
    lut = {c.strip().lower(): c for c in df.columns}
    for cand in candidates:
        if cand.strip().lower() in lut:
            return lut[cand.strip().lower()]
    return None

def add_DT(df):
    """
    Add a unified datetime column 'DT' without dropping source columns.
    Priority:
      1) 'dt' (already in *_Aug.csv)
      2) 'FORECAST_DATE_LOCAL'
      3) 'FORECAST_DATE_GMT' (convert UTC -> America/Edmonton)
      4) 'Date (MST)', 'Date (MPT)', 'Date (MDT)' (for CSD generation datasets)
    """
    df.columns = df.columns.str.strip()
    dt_col = None

    # Recognize all possible time columns
    candidates = [
        "dt", "FORECAST_DATE_LOCAL", "FORECAST_DATE_GMT",
        "Date (MST)", "Date (MPT)", "Date (MDT)"
    ]

    for c in candidates:
        if c in df.columns:
            dt_col = c
            break

    if not dt_col:
        raise KeyError("No datetime column found (dt / FORECAST_DATE_LOCAL / FORECAST_DATE_GMT / Date (MST) / Date (MPT)).")

    # Convert to datetime
    if "GMT" in dt_col:
        dt_utc = pd.to_datetime(df[dt_col], errors="coerce", utc=True)
        df["DT"] = dt_utc.dt.tz_convert("America/Edmonton").dt.tz_localize(None)
    else:
        df["DT"] = pd.to_datetime(df[dt_col], errors="coerce")

    df = df.dropna(subset=["DT"]).sort_values("DT")
    return df
    
def standardize_energy(df, prefix):
    out = df.copy()
    ren = {}
    for src, tgt in [("OPT", f"{prefix}_FORECAST"),
                     ("ACTUAL", f"{prefix}_ACTUAL"),
                     ("MIN", f"{prefix}_MIN"),
                     ("MAX", f"{prefix}_MAX")]:
        c = pick_col(out, [src])
        if c:
            ren[c] = tgt
    out = out.rename(columns=ren)
    for k in ren.values():
        out[k] = pd.to_numeric(out[k], errors="coerce")
    return out

def keep_august_2025(df):
    return df[(df["DT"].dt.year == 2025) & (df["DT"].dt.month == 8)]

def print_daily_counts(tag, df):
    per_day = df["DT"].dt.floor("D").value_counts().sort_index()
    print(f"[{tag}] rows={len(df)}  unique_days={per_day.size}")