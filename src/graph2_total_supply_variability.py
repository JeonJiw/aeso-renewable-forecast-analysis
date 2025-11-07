# -*- coding: utf-8 -*-
"""
Graph 2: Total Supply and 24-hour Rolling Variability for a given year/month

Usage:
  python src/graph2_total_supply_variability.py [--year 2025] [--month 8] [--show|--no-show]
"""

import os
import argparse
import calendar
import pandas as pd
import matplotlib.pyplot as plt
from common import add_DT, keep_month, parse_show_flag, ensure_dirs

# Parse year/month from args or env
parser = argparse.ArgumentParser(add_help=False)
parser.add_argument("--year", type=int, default=int(os.environ.get("YEAR", 2025)))
parser.add_argument("--month", type=int, default=int(os.environ.get("MONTH", 8)))
args, _ = parser.parse_known_args()
YEAR: int = args.year
MONTH: int = args.month
if not (1 <= MONTH <= 12):
    raise SystemExit(f"Invalid month: {MONTH}. Use 1..12")
MM = f"{MONTH:02d}"
MONTH_NAME = calendar.month_name[MONTH]

DATA_FILE = os.path.join("data", f"CSD Generation (Hourly) - {YEAR}-{MM}.csv")
OUT_PNG = os.path.join("figures", f"graph2_total_supply_variability_{YEAR}-{MM}.png")
ensure_dirs(OUT_PNG)

# === Load Data ===
df = pd.read_csv(DATA_FILE)
df.columns = df.columns.str.strip()

# Convert time column
df = add_DT(df)

# Filter to target year/month
df = keep_month(df, YEAR, MONTH)

# === Compute total supply (sum of all assets per hour) ===
supply = df.groupby("DT", as_index=False)["Volume"].sum()
supply = supply.sort_values("DT")

# === Compute 24-hour rolling standard deviation ===
supply["Rolling_Std_24H"] = supply["Volume"].rolling(window=24).std()

# === Plot ===
fig, ax1 = plt.subplots(figsize=(12, 6))

# Total Supply
ax1.plot(supply["DT"], supply["Volume"], color="black", linewidth=1.8, label="Total Supply (MW)")
ax1.set_xlabel("Time")
ax1.set_ylabel("Total Supply (MW)", color="black")
ax1.tick_params(axis="y", labelcolor="black")

# Rolling STD
ax2 = ax1.twinx()
ax2.plot(supply["DT"], supply["Rolling_Std_24H"], color="orange", linewidth=1.6, label="24H Rolling Std")
ax2.set_ylabel("24H Rolling Std (MW)", color="orange")
ax2.tick_params(axis="y", labelcolor="orange")

# Titles and grid
plt.title(f"Total Supply and 24H Rolling Variability — {MONTH_NAME} {YEAR} (AESO Data)")
ax1.grid(alpha=0.3)

# Legends (combined)
lines, labels = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines + lines2, labels + labels2, loc="upper right")

# Save
SHOW = parse_show_flag(default_show=True)  # standalone run = show by default

plt.tight_layout()
plt.savefig(OUT_PNG, dpi=300, bbox_inches="tight")
if SHOW:
    plt.show()
else:
    plt.close()
print(f"[OK] Saved → {OUT_PNG}")