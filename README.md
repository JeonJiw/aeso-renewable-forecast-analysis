# CPSC 3720 – Assignment 2 (AESO)

**Project:** Evaluating Solar and Wind Forecast Accuracy using AESO Data (August 2025)  
**Team (2):**

- Jiwon Jeon — Data Analysis & Visualization & Report Design
- Chloe Lee — Data Processing & Computation & Documentation

## Overview

Analyze forecast accuracy (MAPE, MAE) of solar/wind generation in Alberta and examine how forecast errors relate to total supply variability (24H rolling std).  
Two subplots: (1) Solar/Wind Forecast vs Actual, (2) Total Supply & Rolling Std.

## Repo Structure

- `docs/` – One-page design summary
- `src/` – Python scripts (`aeso_analysis.py`)
- `notebooks/` – Jupyter version
- `figures/` – Generated plots
- `data/` – CSV files (may be git-ignored; see `data/README.md`)

## Data Source (Citations)

- Alberta Electric System Operator (AESO): https://www.aeso.ca/market/market-and-system-reporting/data-requests

## 🧰 Setup Instructions (Recommended: Virtual Environment)

### 1️⃣ Create and Activate Virtual Environment

```bash
cd ~/Projects/aeso-renewable-forecast-analysis
python3 -m venv venv
source venv/bin/activate   # macOS/Linux

```

### 2️⃣ Install Dependencies

```bash
pip install --upgrade pip
pip install pandas matplotlib
```

### ▶️ How to Run

```bash
# From the project root
python src/aeso_analysis.py
# Or, if using the first visualization script:
python src/graph1_forecast_vs_actual.py

```

Output:
Generated figures will be saved to:

```bash
figures/assignment2_aeso_plots.png
```

### 🧾 Notes

    •	Ensure that CSV files (Solar_Data_2025.csv, Wind_Data_2025.csv, CSD Generation (Hourly) - 2025-08.csv) are placed in the data/ directory.
    •	The scripts automatically merge and align time-series data using pandas.merge_asof() based on timestamps.
    •	Forecast accuracy is computed using mean absolute percentage error (MAPE) and mean absolute error (MAE).
