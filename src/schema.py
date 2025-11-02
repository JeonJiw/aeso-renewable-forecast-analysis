"""
Standard schema definition: timestamp / forecast / actual / resource
All analysis/visualization uses these 4 columns as minimum contract.
"""
import pandas as pd
from dataclasses import dataclass

CANONICAL_COLUMNS = ["timestamp", "forecast", "actual", "resource"]

@dataclass
class ValidationResult:
    ok: bool
    missing: list[str]

def validate(df: pd.DataFrame) -> ValidationResult:
    cols = list(df.columns)
    missing = [c for c in CANONICAL_COLUMNS if c not in cols]
    return ValidationResult(ok=len(missing) == 0, missing=missing)

def to_canonical(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert timestamp to datetime, forecast/actual to float, resource to string.
    """
    d = df.copy()
    if "timestamp" in d.columns:
        d["timestamp"] = pd.to_datetime(d["timestamp"], errors="coerce")
    for c in ["forecast", "actual"]:
        if c in d.columns:
            d[c] = pd.to_numeric(d[c], errors="coerce")
    if "resource" in d.columns:
        d["resource"] = d["resource"].astype("string")
    return d