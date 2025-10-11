# -*- coding: utf-8 -*-
"""
Graph 2: Total Supply and 24-hour Rolling Variability — August 2025
"""

import pandas as pd
import matplotlib.pyplot as plt
import os
from common import add_DT, keep_august_2025

DATA_FILE = "data/CSD Generation (Hourly) - 2025-08.csv"
OUT_PNG = "figures/graph2_total_supply_variability.png"

# === Load Data ===
df = pd.read_csv(DATA_FILE)
df.columns = df.columns.str.strip()

# Convert time column
df = add_DT(df)

# Filter August 2025
df = keep_august_2025(df)


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
plt.title("Total Supply and 24H Rolling Variability — August 2025 (AESO Data)")
ax1.grid(alpha=0.3)

# Legends (combined)
lines, labels = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines + lines2, labels + labels2, loc="upper right")

# Save
os.makedirs("figures", exist_ok=True)
plt.tight_layout()
plt.savefig(OUT_PNG, dpi=300)
plt.show()

print(f"[OK] Graph saved → {OUT_PNG}")