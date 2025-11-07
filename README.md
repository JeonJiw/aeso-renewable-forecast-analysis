# CPSC 3720 – Assignment 3 (AESO Renewable Forecast Analysis)

**Author:** Jiwon Jeon
**Team Member:** Jiwon Jeon, Chloe Lee
**Course:** CPSC 3720 – Software Design and Architecture  
**Term:** Fall 2025

---

## 📘 Overview

This project analyzes **solar** and **wind** forecast accuracy and system‑wide generation variability using AESO data.  
It demonstrates a **modular and reusable pipeline** that operates solely through naming conventions and column schemas — no code changes are required for new datasets following the contract.

Outputs:

1. **Graph 1:** Forecast vs Actual (Solar/Wind)
2. **Graph 2:** Total Supply & 24‑hour Rolling Std Deviation
3. **Merged Dataset:** `merged_2025-08.csv`

---

## 🧩 Input Contract — Naming Conventions

|  Dataset                  |  Expected Filename                                 |  Notes                                                                         |
| ------------------------- | -------------------------------------------------- | ------------------------------------------------------------------------------ |
|  Solar Forecast & Actual  |  `data/Solar_Data_<YEAR>.csv`                      |  Yearly file with forecast/actual columns (e.g., `OPT_Solar`, `ACTUAL_Solar`)  |
|  Wind Forecast & Actual   |  `data/Wind_Data_<YEAR>.csv`                       |  Yearly file with forecast/actual columns (e.g., `OPT_Wind`, `ACTUAL_Wind`)    |
|  Total Supply (CSD)       |  `data/CSD Generation (Hourly) - <YEAR>-<MM>.csv`  |  Monthly file with `Total_MW` or `Volume`; required for Graph 2                |

### Column Expectations
- Datetime column: `FORECAST_DATE_LOCAL` or `DateTime_Local`  
- Solar/Wind files must contain forecast and actual numeric columns.  
- CSD file must contain either `Total_MW` or `Volume`.  
- Graph 2 requires the CSD file; no fallback to merged data.

---

## 🔄 Data Flow

|  Step  |  Script                                |  Description                       |  Output                                                                               |
| ------ | -------------------------------------- | ---------------------------------- | ------------------------------------------------------------------------------------- |
|  1     |  `extract_month_data.py`               |  Extracts monthly Solar/Wind data  |  `Solar_Data_<YEAR>_<MM>.csv`, `Wind_Data_<YEAR>_<MM>.csv`, `merged_<YEAR>-<MM>.csv`  |
|  2     |  `graph1_forecast_vs_actual.py`        |  Plots Forecast vs Actual          |  `figures/forecast_vs_actual_<YEAR>-<MM>.png`                                         |
|  3     |  `graph2_total_supply_variability.py`  |  Plots Total Supply & Rolling Std  |  `figures/graph2_total_supply_variability_<YEAR>-<MM>.png`                            |

---

## ▶️ How to Run

```bash
# Run entire pipeline for August 2025
python src/run_full_analysis.py 2025 8
```

### Run individual modules

```bash
# Extract monthly data
python src/extract_month_data.py --year 2025 --month 8

# Graph 1 (Forecast vs Actual)
python src/graph1_forecast_vs_actual.py --year 2025 --month 8 --show

# Graph 2 (Total Supply & Variability)
python src/graph2_total_supply_variability.py --year 2025 --month 8 --show
```

---

## ♻️ Reusability and Extensibility

The framework is **data‑agnostic** and uses naming conventions as the input contract.  
Any dataset matching the schema and naming pattern can be analyzed without editing code.

Benefits:
- Plug‑and‑play datasets for different months or years  
- Easily extendable to new providers (e.g., other grid operators)  
- Consistent output structure for automation and reporting

Example:

```bash
# To analyze July 2026
data/Solar_Data_2026.csv
data/Wind_Data_2026.csv
data/CSD Generation (Hourly) - 2026-07.csv

python src/run_full_analysis.py 2026 7
```

---

## 📊 Outputs

|  Type            |  Example                                                |  Purpose                            |
| ---------------- | ------------------------------------------------------- | ----------------------------------- |
|  Merged Dataset  |  `data/merged_2025-08.csv`                              |  Combined solar/wind data           |
|  Graph 1         |  `figures/forecast_vs_actual_2025-08.png`               |  Compare forecast vs actual         |
|  Graph 2         |  `figures/graph2_total_supply_variability_2025-08.png`  |  Show total supply and variability  |

---

## ⚙️ Technical Notes

- Uses `pandas.merge_asof()` for ±30 min time alignment  
- 24‑hour rolling std computed via `rolling(window=24).std()`  
- `common.py` provides helpers (`add_DT`, `keep_month`, `ensure_dirs`)  
- Matplotlib auto‑switches backend for headless mode

---

**© 2025 — University of Lethbridge | CPSC 3720 Assignment 3**
