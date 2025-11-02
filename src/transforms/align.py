from __future__ import annotations
import pandas as pd

def align_asof(
    left: pd.DataFrame,
    right: pd.DataFrame,
    *,
    on: str = "timestamp",
    by: str | None = None,
    tol: str = "30min",
    suffixes: tuple[str, str] = ("_l", "_r"),
) -> pd.DataFrame:
    """
    Time axis alignment with asof join (nearest match).
    - by: only sort by "resource" if same resource only
    - tol: allowed tolerance (e.g. "30min", "5min")
    Returns: left-aligned dataframe with right-aligned data appended.
    """
    l = left.sort_values(on).copy()
    r = right.sort_values(on).copy()
    if by:
        out = pd.merge_asof(
            l, r, on=on, by=by, tolerance=pd.Timedelta(tol), suffixes=suffixes
        )
    else:
        out = pd.merge_asof(
            l, r, on=on, tolerance=pd.Timedelta(tol), suffixes=suffixes
        )
    return out

def split_forecast_actual(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Create two dataframes from standard long format (df) with forecast/actual as value columns.
    Useful for asof alignment etc.
    """
    cols = ["timestamp", "resource"]
    f = df[cols + ["forecast"]].rename(columns={"forecast": "value"})
    a = df[cols + ["actual"]  ].rename(columns={"actual":   "value"})
    return f, a