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


# --- Plot show/hide control ---
import argparse, os

def parse_show_flag(default_show=True):
    """
    Handle whether to display matplotlib window or not.
    - default_show: True when running standalone
    - If RUN_PIPELINE=1 → default_show=False (for batch runs)
    - CLI flags override:
        --show     → always show
        --no-show  → always hide
    """
    p = argparse.ArgumentParser(add_help=False)
    g = p.add_mutually_exclusive_group()
    g.add_argument("--show",    action="store_true")
    g.add_argument("--no-show", action="store_true")
    args, _ = p.parse_known_args()

    # hide by default in pipeline mode
    if os.environ.get("RUN_PIPELINE") == "1":
        default_show = False

    if args.show:
        return True
    if args.no_show:
        return False
    return default_show

def ensure_dirs(path):
    """
    Ensure the directory for the given path exists.
    Accepts either a file path (creates parent) or a directory path.
    """
    import os
    dirpath = path if os.path.splitext(path)[1] == "" else os.path.dirname(path)
    if dirpath and not os.path.exists(dirpath):
        os.makedirs(dirpath, exist_ok=True)