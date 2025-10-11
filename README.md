# CPSC 3720 – Assignment 2 (AESO)

**Project:** Evaluating Solar & Wind Forecast Accuracy using AESO Data (August 2025)

**Team :**

- **Jiwon Jeon** — Data Analysis, Visualization, Report Design
- **Chloe Lee** — Data Processing, Computation, Documentation

---

## 📘 Overview

This project evaluates **solar** and **wind** forecast accuracy in Alberta using AESO data, focusing on:

- Forecast accuracy metrics (MAE, MAPE, in-range coverage)
- Relationship between **forecast errors** and **system variability** (24-hour rolling standard deviation of total supply)

Deliverables include:

1. **Graph 1:** Forecast vs Actual (Solar=Red, Wind=Blue)
2. **Graph 2:** Total Supply & 24H Rolling Std
3. **Metrics:** Hourly/Daily CSVs (errors, coverage, variability)
4. **Dashboard:** “System Variability vs Forecast Stability” visualization

---

## 📂 Repository Structure

```
data/                         # Input CSVs and derived *_Aug.csv
figures/                      # Generated plots
analysis/                     # Generated metrics CSVs
src/
  common.py
  extract_august_data.py
  graph1_forecast_vs_actual.py
  graph2_total_supply_variability.py
  analysis_metrics_aug2025.py
  plot_stability_comparison.py
  run_full_analysis.py        # Orchestrates all scripts
docs/                         # Design summary & final analysis notes
```

---

## 📊 Data Source

- Alberta Electric System Operator (AESO):  
  https://www.aeso.ca/market/market-and-system-reporting/data-requests

---

## ⚙️ Setup Instructions

### 1️⃣ Create & Activate Virtual Environment

```bash
cd ~/Projects/aeso-renewable-forecast-analysis
python3 -m venv venv
source venv/bin/activate     # macOS/Linux
```

### 2️⃣ Install Dependencies

```bash
pip install --upgrade pip
pip install pandas matplotlib
```

---

## ▶️ How to Run the Full Pipeline

```bash
# from project root
python src/run_full_analysis.py
```

### 🔄 Pipeline Steps

| Step | Description                                  | Output                                                                      |
| ---- | -------------------------------------------- | --------------------------------------------------------------------------- |
| 1    | Extract August 2025 Data                     | `Solar_Data_2025_Aug.csv`, `Wind_Data_2025_Aug.csv`                         |
| 2    | Graph 1 — Forecast vs Actual                 | `figures/forecast_vs_actual_aug2025.png`                                    |
| 3    | Graph 2 — Total Supply & Rolling Variability | `figures/graph2_total_supply_variability.png`                               |
| 4    | Compute Analysis Metrics                     | `analysis/metrics_aug2025_hourly.csv`, `analysis/metrics_aug2025_daily.csv` |
| 5    | Final Dashboard (Main Output)                | `figures/stability_comparison.png` (shown)                                  |

> When running the full pipeline, only the **final dashboard** is displayed.  
> Intermediate graphs are saved silently.

---

## ▶️ Run Individually (For Debugging)

```bash
# 1. Extract August data (creates *_Aug.csv)
python src/extract_august_data.py

# 2. Graph 1 (Forecast vs Actual)
python src/graph1_forecast_vs_actual.py --show

# 3. Graph 2 (Total Supply & Variability)
python src/graph2_total_supply_variability.py --show

# 4. Analysis Metrics (generate CSVs)
python src/analysis_metrics_aug2025.py

# 5. Stability Comparison Dashboard
python src/plot_stability_comparison.py --show
```

---

## 📦 Input Files

Place the following in the `data/` directory:

- `Solar_Data_2025.csv`
- `Wind_Data_2025.csv`
- `CSD Generation (Hourly) - 2025-08.csv`

Generated automatically:

- `Solar_Data_2025_Aug.csv`, `Wind_Data_2025_Aug.csv`
- `merged_aug2025.csv`

---

## 📈 Metrics Description

### Hourly Metrics (`metrics_aug2025_hourly.csv`)

| Column              | Description                                 |
| ------------------- | ------------------------------------------- |
| DT                  | Timestamp (hourly)                          |
| SOLAR/WIND_FORECAST | Forecast generation (MW)                    |
| SOLAR/WIND_ACTUAL   | Actual generation (MW)                      |
| AE, APE\_%          | Absolute Error, Absolute Percentage Error   |
| IN_RANGE            | Whether actual lies within forecast range   |
| TOTAL_SUPPLY_MW     | System total generation                     |
| ROLLING_STD_24H     | 24-hour rolling variability of total supply |

### Daily Metrics (`metrics_aug2025_daily.csv`)

| Column                | Description                         |
| --------------------- | ----------------------------------- |
| date                  | Day (local time)                    |
| SOLAR/WIND_MAE, MAPE% | Mean errors for each source         |
| Coverage%             | Forecast range accuracy             |
| RollingStd24h         | Daily average of system variability |

---

## 🧠 Key Insights (Summary)

- **Wind forecasts** show **lower error and higher stability** compared to solar.
- **Solar generation** fluctuates strongly with daylight, leading to higher forecast errors during high variability periods.
- **High total supply variability (rolling std)** correlates with larger solar forecast errors, but not as much for wind.
- Overall, **wind generation contributes to system stability**, particularly during periods of high demand variability.

---

## 🧾 Technical Notes

- Time alignment uses `pandas.merge_asof()` with ±30 min tolerance.
- Variability calculated with `rolling(window=24).std()` over hourly totals.
- During pipeline execution, environment variables are used:
  - `RUN_PIPELINE=1` and `MPLBACKEND=Agg` hide intermediate plots.
  - Direct script runs display figures unless `--no-show` flag is set.

---

✅ **Final Deliverables**

- `figures/stability_comparison.png` (main visualization)
- `analysis/metrics_aug2025_hourly.csv`
- `analysis/metrics_aug2025_daily.csv`
- `docs/` summary report

---

**© 2025 — University of Lethbridge | CPSC 3720 Assignment 2**
