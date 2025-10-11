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
- `notebooks/` – (optional) Jupyter version
- `figures/` – Generated plots
- `data/` – CSV files (may be git-ignored; see `data/README.md`)

## Data Source (Citations)

- Alberta Electric System Operator (AESO): https://www.aeso.ca/market/market-and-system-reporting/data-requests

## How to Run

\`\`\`bash
pip install pandas matplotlib
python src/aeso_analysis.py
\`\`\`
Outputs: `figures/assignment2_aeso_plots.png`
