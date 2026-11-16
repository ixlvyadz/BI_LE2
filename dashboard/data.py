"""Data access: load the cleaned table, hold dimension orders, apply the sidebar filters."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

BASE = Path(__file__).resolve().parent.parent
RAW_PATH = BASE / "data" / "healthcare_operations_raw.csv"
CLEAN_PATH = BASE / "data" / "healthcare_operations_clean.csv"
REPORT_PATH = BASE / "data" / "data_quality_report.json"
MODEL_DIR = BASE / "data" / "model"

SEVERITY_ORDER = ["Low", "Moderate", "High", "Critical"]
SHIFT_ORDER = ["Day", "Evening", "Night"]
DOW_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
AGE_ORDER = ["Pediatric (0-17)", "Adult (18-44)", "Middle Age (45-64)", "Senior (65+)"]
SETTING_ORDER = ["Inpatient", "Emergency", "Ambulatory & Diagnostic"]
STATUS_ORDER = ["Stable", "Moderate Risk", "High Strain"]
MONTH_ORDER = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
WAIT_BANDS = ["0-15 min", "15-35 min", "35-60 min", "Over 60 min"]

# natural orders for ordinal dimensions (anything not listed is ranked by value)
ORDINAL = {
    "severity_level": SEVERITY_ORDER, "shift": SHIFT_ORDER, "day_of_week": DOW_ORDER, "age_group": AGE_ORDER,
    "care_setting": SETTING_ORDER, "capacity_status": STATUS_ORDER, "wait_band": WAIT_BANDS,
}

# dimensions offered in the "Compare by" controls
DIMENSIONS = {
    "Department": "department", "Care setting": "care_setting", "Shift": "shift", "Severity": "severity_level",
    "Admission type": "admission_type", "Insurance": "insurance_type", "Age group": "age_group",
    "Provider": "provider_type", "Day of week": "day_of_week",
}

SHORT = {
    "Emergency Department (ED)": "Emergency (ED)",
    "Outpatient / Ambulatory Care": "Outpatient",
    "Ambulatory & Diagnostic": "Ambulatory & Dx",
    "Middle Age (45-64)": "Middle age (45-64)",
}


def short(label) -> str:
    return SHORT.get(str(label), str(label))


@st.cache_data(show_spinner=False)
def load_data() -> pd.DataFrame:
    if not CLEAN_PATH.exists():  # first run on a fresh clone: build the cleaned files
        import data_prep
        data_prep.main()
    df = pd.read_csv(CLEAN_PATH, parse_dates=["visit_date", "month_start"])
    df["wait_band"] = pd.cut(
        df["er_wait_time_minutes"], [-0.01, 15, 35, 60, 10_000], labels=WAIT_BANDS
    ).astype(str)
    return df


@st.cache_data(show_spinner=False)
def load_raw() -> pd.DataFrame:
    return pd.read_csv(RAW_PATH)


@st.cache_data(show_spinner=False)
def load_report() -> dict:
    return json.loads(REPORT_PATH.read_text())


@st.cache_data(show_spinner=False)
def load_model_table(name: str) -> pd.DataFrame:
    return pd.read_csv(MODEL_DIR / f"{name}.csv")


def apply_filters(df: pd.DataFrame, f: dict) -> pd.DataFrame:
    """Apply every sidebar slicer. An empty selection means 'all'."""
    m = (df["month"] >= f["period"][0]) & (df["month"] <= f["period"][1])
    for col, key in [
        ("care_setting", "setting"), ("department", "department"), ("admission_type", "admission"),
        ("severity_level", "severity"), ("shift", "shift"), ("insurance_type", "insurance"), ("age_group", "age"),
    ]:
        if f.get(key):
            m &= df[col].isin(f[key])
    if f.get("day") == "Weekday":
        m &= df["is_weekend"] == "No"
    elif f.get("day") == "Weekend":
        m &= df["is_weekend"] == "Yes"
    return df[m]


def count_active(f: dict, full_period: tuple[str, str]) -> int:
    n = sum(bool(f.get(k)) for k in ["setting", "department", "admission", "severity", "shift", "insurance", "age"])
    n += int(tuple(f["period"]) != tuple(full_period))
    n += int(f.get("day") not in (None, "All"))
    return n


def period_label(month: str) -> str:
    return pd.Period(month, freq="M").strftime("%b %Y")
