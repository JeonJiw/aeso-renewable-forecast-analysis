# -*- coding: utf-8 -*-
"""
Make 'Stability Comparison' charts from metrics CSVs (no raw/merged reads).

Inputs (from analysis_metrics_aug2025.py):
  - analysis/metrics_aug2025_hourly.csv   (required)
  - analysis/metrics_aug2025_daily.csv    (optional)

Outputs:
  - figures/stability_comparison.png
  - figures/stability_comparison_daily.png  (if daily CSV exists)

Run:
  source venv/bin/activate
  python src/plot_stability_comparison.py [--show|--no-show]
"""

import os
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

AN_DIR = "analysis"
FIG_DIR = "figures"
os.makedirs(FIG_DIR, exist_ok=True)

HOURLY_CSV = os.path.join(AN_DIR, "metrics_aug2025_hourly.csv")
DAILY_CSV  = os.path.join(AN_DIR, "metrics_aug2025_daily.csv")
OUT_HOURLY = os.path.join(FIG_DIR, "stability_comparison.png")
OUT_DAILY  = os.path.join(FIG_DIR, "stability_comparison_daily.png")

def parse_show_flag(default_show=True):
    p = argparse.ArgumentParser(add_help=False)
    g = p.add_mutually_exclusive_group()
    g.add_argument("--show",    action="store_true")
    g.add_argument("--no-show", action="store_true")
    args, _ = p.parse_known_args()
    if os.environ.get("RUN_PIPELINE") == "1":
        default_show = False
    if args.show: return True
    if args.no_show: return False
    return default_show

def load_hourly(path: str) -> pd.DataFrame:
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Missing {path}. Build metrics first.")
    df = pd.read_csv(path, parse_dates=["DT"])
    df = df.sort_values("DT").reset_index(drop=True)
    return df

def stability_comparison_from_hourly(df: pd.DataFrame, out_png: str, show: bool):
    SOLAR = "#d62728"
    WIND  = "#1f77b4"
    VOL   = "orange"

    need_cols = ["DT", "ROLLING_STD_24H", "SOLAR_AE", "WIND_AE"]
    missing = [c for c in need_cols if c not in df.columns]
    if missing:
        raise KeyError(f"Hourly metrics missing columns: {missing}")

    fig, axes = plt.subplots(3, 1, figsize=(14, 9), sharex=True)
    fig.suptitle("Forecast Stability vs System Variability — August 2025 (from hourly metrics)")

    # 1) System Variability
    axes[0].plot(df["DT"], df["ROLLING_STD_24H"], color=VOL, linewidth=1.8, label="System Variability (24H Rolling Std)")
    axes[0].set_ylabel("Variability (MW)")
    axes[0].grid(alpha=0.3)
    axes[0].legend(loc="upper right")

    # 2) Solar Forecast Error (AE)
    axes[1].plot(df["DT"], df["SOLAR_AE"], color=SOLAR, linewidth=1.6, label="Solar Forecast Error (AE)")
    axes[1].set_ylabel("Solar AE (MW)")
    axes[1].grid(alpha=0.3)
    axes[1].legend(loc="upper right")

    # 3) Wind Forecast Error (AE)
    axes[2].plot(df["DT"], df["WIND_AE"], color=WIND, linewidth=1.6, label="Wind Forecast Error (AE)")
    axes[2].set_ylabel("Wind AE (MW)")
    axes[2].set_xlabel("Time")
    axes[2].grid(alpha=0.3)
    axes[2].legend(loc="upper right")

    # Optional highlight: top 15% volatility windows
    if df["ROLLING_STD_24H"].notna().any():
        thr = np.nanpercentile(df["ROLLING_STD_24H"].values, 85)
        high = df["ROLLING_STD_24H"] >= thr
        in_block = False
        start = None
        for i in range(len(df)):
            if high.iloc[i] and not in_block:
                in_block = True
                start = df["DT"].iloc[i]
            if (not high.iloc[i] and in_block) or (in_block and i == len(df)-1):
                end = df["DT"].iloc[i]
                for ax in axes:
                    ax.axvspan(start, end, color="gray", alpha=0.10)
                in_block = False

    fig.tight_layout(rect=[0, 0, 1, 0.97])
    fig.savefig(out_png, dpi=300, bbox_inches="tight")
    if show:
        plt.show()
    plt.close(fig)
    print(f"[OK] saved → {out_png}")

def daily_trend_optional(path: str, out_png: str, show: bool):
    if not os.path.isfile(path):
        return
    d = pd.read_csv(path, parse_dates=["date"])
    d = d.sort_values("date").reset_index(drop=True)

    cols = d.columns
    have = {
        "SOLAR_MAE": "Solar MAE (MW)",
        "WIND_MAE": "Wind MAE (MW)",
        "SOLAR_MAPE%": "Solar MAPE (%)",
        "WIND_MAPE%": "Wind MAPE (%)",
        "RollingStd24h": "Rolling Std (MW)",
    }
    ycols = [k for k in have if k in cols]
    if not ycols:
        return

    fig, ax1 = plt.subplots(figsize=(12, 6))
    ax1.set_title("Daily Accuracy vs System Variability — August 2025")
    ax1.set_xlabel("Date")

    handles, labels = [], []
    if "SOLAR_MAE" in cols:
        h1, = ax1.plot(d["date"], d["SOLAR_MAE"], color="#d62728", linewidth=1.8, label="Solar MAE (MW)")
        handles.append(h1); labels.append("Solar MAE (MW)")
    if "WIND_MAE" in cols:
        h2, = ax1.plot(d["date"], d["WIND_MAE"], color="#1f77b4", linewidth=1.8, label="Wind MAE (MW)")
        handles.append(h2); labels.append("Wind MAE (MW)")
    ax1.set_ylabel("MAE (MW)")
    ax1.grid(alpha=0.3)

    if "RollingStd24h" in cols:
        ax2 = ax1.twinx()
        h3, = ax2.plot(d["date"], d["RollingStd24h"], color="orange", linewidth=1.6, label="Rolling Std (MW)")
        ax2.set_ylabel("Rolling Std (MW)", color="orange")
        ax2.tick_params(axis="y", labelcolor="orange")
        handles.append(h3); labels.append("Rolling Std (MW)")

    if handles:
        ax1.legend(handles=handles, labels=labels, loc="upper right")

    fig.tight_layout()
    fig.savefig(out_png, dpi=300, bbox_inches="tight")
    if show:
        plt.show()
    plt.close(fig)
    print(f"[OK] saved → {out_png}")

if __name__ == "__main__":
    SHOW = parse_show_flag(default_show=True)
    hourly = load_hourly(HOURLY_CSV)
    stability_comparison_from_hourly(hourly, OUT_HOURLY, SHOW)
    daily_trend_optional(DAILY_CSV, OUT_DAILY, SHOW)