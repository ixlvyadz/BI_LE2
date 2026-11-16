# HealthOps BI: Healthcare Operations Dashboard

CS 313 Business Intelligence, Final Learning Evidence.
An interactive BI dashboard for hospital operations built with Python, Streamlit and Plotly
(custom HTML/CSS for the layout and KPI cards).

Domain: **Healthcare Operations Dashboard** (patient visits, service utilization, waiting times, resource allocation).
Data: 950 simulated, anonymised visits, January 2024 to December 2026, 41 raw fields.

## Run it locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

The app opens at http://localhost:8501.

## Deploy on Streamlit Community Cloud

1. Create a GitHub repository and upload everything in this folder (keep the folder structure).
2. Go to https://share.streamlit.io, sign in with GitHub and choose **Create app**.
3. Pick the repository and branch, set **Main file path** to `app.py`, and under *Advanced settings* choose Python 3.12 or 3.13.
4. Click **Deploy**. The public link it gives you is the dashboard link for the deliverables.

## What is in the folder

| Path | Purpose |
|---|---|
| `app.py` | Entry point: page navigation and the sidebar slicers |
| `dashboard/pages.py` | The eight pages |
| `dashboard/charts.py` | Plotly chart builders (one shared style) |
| `dashboard/kpi.py` | KPI catalogue: formula, purpose, interpretation, target, calculation |
| `dashboard/insights.py` | Business insights generated from the data in scope |
| `dashboard/theme.py` | Colours, CSS, HTML building blocks |
| `dashboard/docs.py` | Business case, data dictionary, star-schema diagram |
| `data_prep.py` | Reproducible cleaning and modelling pipeline (`python data_prep.py`) |
| `data/healthcare_operations_raw.csv` | Raw dataset (deliverable) |
| `data/healthcare_operations_clean.csv` | Cleaned dataset (deliverable) |
| `data/model/` | Star schema: `fact_visits`, eight `dim_*` tables, one bridge table |
| `data/data_quality_report.json` | Before/after profile and the log of every cleaning step |
| `screenshots/` | Dashboard screenshots (deliverable) |

## Pages

| Page | Business question |
|---|---|
| Overview | Which targets are met or missed? 8 KPI cards, trend, capacity status, department scorecard |
| Patient flow | When do patients arrive and where do they wait longest? |
| Capacity | Which units are over the occupancy ceiling and what causes the strain? |
| Quality | Who is readmitted and where is treatment success weakest? |
| Cost | Where does cost concentrate and what drives cost per visit? |
| Drill-down | Click a bar: care setting, then department, then individual visit records |
| Insights & actions | Eight insights, each with discovery, evidence, importance and recommended action |
| Data & methods | Business case, cleaning log, data model, KPI definitions, data dictionary, downloads |

## BI features

- **Slicers** (apply to every page): period, care setting, department, severity, shift, weekday/weekend, admission type, insurance, age group; one-click reset.
- **KPI cards** with target status, change against the previous year (like for like) and sparklines.
- **Drill-down** by clicking bars, with breadcrumbs, plus a visit-level table with search and CSV download.
- **Per-chart controls**: KPI, time grain and compare-by pickers; hover tooltips; a "View data" table behind every chart.
- **Insights recalculate** with the filters, so the text always matches the charts.

## Data preparation summary

| Issue | Rows | Treatment |
|---|---|---|
| Leading/trailing spaces in department | 5 | Trimmed |
| Inconsistent department spelling/casing (22 labels) | 15 | Mapped to 10 canonical names |
| Duplicate rows or visit IDs | 0 | Checked, none found |
| Missing `estimated_cost_per_visit` | 8 | Recovered exactly from `department_cost_burden / (resource_utilization_index / 100)` |
| Missing `patient_satisfaction_score` | 10 | Department median, flagged in `satisfaction_imputed` |
| Multi-valued `bottleneck_reason` | 435 | Split into a bridge table |
| Derived fields and ranges | 0 failures | 10 validation rules, all pass |

## KPIs (targets come from the dataset)

Patient visits; average wait time (target 35 min or less); bed occupancy (85% or less); 30-day readmission (12% or less);
no-show rate (10% or less); patient satisfaction (4.2 or more); treatment success (88% or more); average cost per visit.
Formula, purpose and interpretation of each are on the *Data & methods* page and in `dashboard/kpi.py`.
