"""
Common metrics calculation module: MAE, MAPE, Coverage
"""
import pandas as pd
import numpy as np

def mae(forecast: pd.Series, actual: pd.Series) -> float:
    return float((forecast - actual).abs().mean())

def mape(forecast: pd.Series, actual: pd.Series) -> float:
    denom = actual.abs().clip(lower=1e-9)
    return float(((forecast - actual).abs() / denom).mean() * 100.0)

def coverage(df: pd.DataFrame, band: float = 0.1) -> float:
    """
    Calculate percentage of actual values within ±band% of forecast.
    """
    lower = df["forecast"] * (1 - band)
    upper = df["forecast"] * (1 + band)
    in_range = ((df["actual"] >= lower) & (df["actual"] <= upper)).mean()
    return float(in_range * 100.0)