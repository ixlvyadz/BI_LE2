"""Reference text shown on the Data & methods page: business context, data dictionary, model diagram."""
from __future__ import annotations

BUSINESS = {
    "Background": (
        "A general hospital with ten departments (emergency, inpatient units, ICU, surgery and diagnostic / ambulatory "
        "services). The extract covers 950 anonymised patient visits from January 2024 to December 2026."
    ),
    "Business problem": (
        "Operations are monitored through spreadsheets and manual reports, so managers cannot see in one place where "
        "patients wait too long, which units are over capacity, where quality targets are missed or where cost concentrates."
    ),
    "General objective": (
        "Build an interactive BI dashboard that turns the raw visit data into monitored KPIs and actionable insights "
        "for hospital management."
    ),
}

SPECIFIC_OBJECTIVES = [
    "Clean and model the visit data into a star schema ready for analysis.",
    "Track patient volume, wait time, bed occupancy, readmission, no-show, satisfaction, treatment success and cost against targets.",
    "Compare performance by department, shift, severity, admission type, insurer and time.",
    "Identify bottlenecks and the groups that drive them.",
    "Give management evidence-based recommendations.",
]

BUSINESS_QUESTIONS = [
    ("Which targets is the hospital meeting, and which is it missing?", "Overview"),
    ("When do patients arrive, and where do they wait longest?", "Patient flow"),
    ("Which units are over the occupancy ceiling, and what is causing the strain?", "Capacity"),
    ("Who is readmitted, and where is treatment success weakest?", "Quality"),
    ("Where does the money go, and what drives cost per visit?", "Cost"),
    ("How does any one department perform in detail?", "Drill-down"),
    ("What should management do next?", "Insights"),
]

USERS = [
    ("Hospital administrator / COO", "Overall performance against targets; where to intervene."),
    ("Department heads", "Their unit's wait, occupancy, outcomes and cost versus the others."),
    ("Nursing and bed managers", "Shift-level demand, occupancy and bottlenecks for staffing."),
    ("Quality and patient-safety team", "Readmissions, treatment success, satisfaction."),
    ("Finance", "Cost per visit and where cost concentrates."),
]

# column -> (group, description)
DICTIONARY = [
    ("patient_id", "Identifier", "Anonymised patient key (one visit per patient in this extract)."),
    ("visit_id", "Identifier", "Unique visit key; the grain of the fact table."),
    ("visit_date", "Date", "Date of the visit."),
    ("year / month / quarter", "Date", "Calendar fields derived from visit_date (validated against it)."),
    ("day_of_week / is_weekend", "Date", "Weekday name and weekend flag (Yes / No)."),
    ("department", "Dimension", "Treating department; 22 raw spellings standardised to 10."),
    ("care_setting", "Calculated", "Department group: Inpatient, Emergency, Ambulatory & Diagnostic."),
    ("admission_type", "Dimension", "Emergency, Referral, Scheduled, Transfer or Walk-in."),
    ("insurance_type", "Dimension", "Commercial, Medicaid, Medicare, Private or Self-Pay."),
    ("severity_level", "Dimension", "Low, Moderate, High or Critical."),
    ("shift", "Dimension", "Day, Evening or Night."),
    ("provider_type", "Dimension", "Care Team, Nurse Practitioner, Physician, Specialist or Technician."),
    ("age / age_group", "Dimension", "Patient age and its band (Pediatric, Adult, Middle Age, Senior)."),
    ("length_of_stay_days", "Measure", "Days from admission to discharge."),
    ("er_wait_time_minutes", "Measure", "Minutes waited before being seen (recorded for every department)."),
    ("throughput_time_hours", "Measure", "Total hours from arrival to departure."),
    ("bed_occupancy_rate", "Measure", "Unit occupancy (%) at the time of the visit."),
    ("resource_utilization_index", "Measure", "0-100 composite of staff, room and equipment use."),
    ("capacity_strain_score", "Measure", "0-100 composite strain score for the visit."),
    ("estimated_cost_per_visit", "Measure", "Estimated cost of the visit; 8 blanks recovered from related fields."),
    ("department_cost_burden", "Measure", "Cost x resource utilization / 100."),
    ("patient_satisfaction_score", "Measure", "Survey score 1-5; 10 blanks filled with the department median."),
    ("appointment_completed", "Flag", "1 if the visit was completed as planned."),
    ("no_show", "Flag", "1 if the patient did not attend."),
    ("readmitted_30_days", "Flag", "1 if readmitted within 30 days."),
    ("treatment_success", "Flag", "1 if treatment was recorded as successful."),
    ("visit_outcome / discharge_status", "Attribute", "Outcome and discharge destination of the visit."),
    ("capacity_status", "Attribute", "Stable, Moderate Risk or High Strain."),
    ("operational_risk_level", "Attribute", "Low, Moderate or High."),
    ("hospital_alert_flag", "Attribute", "Green, Orange or Red alert in force."),
    ("bottleneck_reason", "Attribute", "One or more bottleneck causes separated by ';' (split into a bridge table)."),
    ("target_* (6 columns)", "Target", "Hospital-wide targets: occupancy 85%, readmission 12%, wait 35 min, no-show 10%, satisfaction 4.2, success 88%."),
    ("wait_over_target", "Calculated", "1 if er_wait_time_minutes > target_er_wait_time."),
    ("occupancy_over_target", "Calculated", "1 if bed_occupancy_rate > target_bed_occupancy_rate."),
    ("high_strain", "Calculated", "1 if capacity_status = 'High Strain'."),
    ("bottleneck_count", "Calculated", "Number of bottleneck reasons on the visit (0 if none)."),
    ("month_start / month_name / month_num", "Calculated", "Helper date fields for trend and seasonality charts."),
    ("cost_imputed / satisfaction_imputed", "Calculated", "1 where the value was filled during cleaning (audit trail)."),
]

RELATIONSHIPS = [
    ("fact_visits.date_key", "dim_date.date_key", "many-to-one"),
    ("fact_visits.department_key", "dim_department.department_key", "many-to-one"),
    ("fact_visits.patient_id", "dim_patient.patient_id", "many-to-one"),
    ("fact_visits.admission_key", "dim_admission_type.admission_key", "many-to-one"),
    ("fact_visits.severity_key", "dim_severity.severity_key", "many-to-one"),
    ("fact_visits.shift_key", "dim_shift.shift_key", "many-to-one"),
    ("fact_visits.provider_key", "dim_provider_type.provider_key", "many-to-one"),
    ("fact_visits.insurance_key", "dim_insurance_type.insurance_key", "many-to-one"),
    ("bridge_visit_bottleneck.visit_id", "fact_visits.visit_id", "many-to-one"),
]


def model_dot(tables: dict) -> str:
    """Graphviz DOT for the star schema (fact in the middle, dimensions around it)."""
    dims = [
        ("dim_date", "date_key (PK)\\lvisit_date, year, quarter,\\lmonth, day_of_week, is_weekend\\l"),
        ("dim_department", "department_key (PK)\\ldepartment, care_setting\\l"),
        ("dim_patient", "patient_id (PK)\\lage, age_group\\l"),
        ("dim_admission_type", "admission_key (PK)\\ladmission_type\\l"),
        ("dim_severity", "severity_key (PK)\\lseverity_level, rank\\l"),
        ("dim_shift", "shift_key (PK)\\lshift, rank\\l"),
        ("dim_provider_type", "provider_key (PK)\\lprovider_type\\l"),
        ("dim_insurance_type", "insurance_key (PK)\\linsurance_type\\l"),
    ]
    rows = lambda t: f"{tables.get(t, {}).get('rows', 0):,} rows"  # noqa: E731
    out = [
        "graph star {",
        '  layout=neato; overlap=false; splines=true; bgcolor="transparent"; pad=0.2;',
        '  node [shape=box, style="rounded,filled", fontname="Helvetica", fontsize=10, margin="0.16,0.10", '
        'color="#c9d2df", fillcolor="#ffffff", fontcolor="#0f1f33"];',
        '  edge [color="#86b6ef", penwidth=1.6];',
        f'  fact_visits [label="fact_visits  ({rows("fact_visits")})\\l\\lvisit_id (PK)\\l8 foreign keys\\l'
        'measures: wait, LOS, occupancy,\\lutilization, strain, cost, satisfaction\\l'
        'flags: completed, no_show,\\lreadmitted, success, over-target\\l", '
        'fillcolor="#2a78d6", fontcolor="#ffffff", color="#1c5cab", fontsize=11, pos="0,0!"];',
    ]
    import math
    for i, (name, cols) in enumerate(dims):
        ang = 2 * math.pi * i / len(dims) + math.pi / 8
        x, y = 4.3 * math.cos(ang), 2.5 * math.sin(ang)
        out.append(f'  {name} [label="{name}  ({rows(name)})\\l\\l{cols}", pos="{x:.2f},{y:.2f}!"];')
        out.append(f"  fact_visits -- {name};")
    out.append(
        f'  bridge [label="bridge_visit_bottleneck  ({rows("bridge_visit_bottleneck")})\\l\\lvisit_id (FK)\\lbottleneck\\l", '
        'fillcolor="#e8f1fd", pos="0,-3.6!"];'
    )
    out.append('  fact_visits -- bridge [style=dashed];')
    out.append("}")
    return "\n".join(out)
