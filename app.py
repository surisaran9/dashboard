import streamlit as st
import pandas as pd
import plotly.express as px

# ─── 0. PAGE CONFIG ──────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Medicare STAR Rating Simulator",
    layout="wide"
)

# ─── HEADER: LOGO LEFT, TITLE CENTERED BELOW ────────────────────────────────
logo_path = "logo.png"  # your 365×138 logo next to app.py

# Row 1: Logo in left column
col1, col2, col3 = st.columns([1, 6, 1])
with col1:
    st.image(logo_path, width=365)
with col2:
    st.empty()
with col3:
    st.empty()

# Row 2: Title centered across the page
_, title_col, _ = st.columns([1, 6, 1])
with title_col:
    st.markdown(
        "<h1 style='text-align:center; margin-top:20px;'>"
        "Medicare STAR Rating Simulator"
        "</h1>",
        unsafe_allow_html=True
    )

# === 1. KPI definitions ===
categorized_kpis = {
    "Part D Measures": {
        "Medication Adherence": {
            "Medication Adherence - Diabetes": "Percentage of members with diabetes who adhere to their medication regimen.",
            "Medication Adherence - Hypertension": "Percentage of members with high blood pressure who take their meds as prescribed.",
            "Medication Adherence - Cholesterol": "Statin adherence among members with cardiovascular risk."
        },
        "High-Risk Medication Use": {
            "Use of High-Risk Medications in the Elderly": "Minimizing risky medications prescribed to older adults."
        },
        "MTM Program Completion Rate": {
            "MTM Program Completion Rate for CMR": "Percent of members who completed a Comprehensive Medication Review."
        }
    },
    "Member Experience (CAHPS)": {
        "Access and Service": {
            "Getting Needed Care": "Members' ease of getting appointments and services.",
            "Getting Appointments and Care Quickly": "Timeliness of access to care."
        },
        "Customer Service": {
            "Customer Service Rating": "Satisfaction with plan's customer service interactions."
        }
    },
    "Member Complaints and Improvement": {
        "Complaints and Disenrollment": {
            "Members Choosing to Leave the Plan": "Rate at which members voluntarily leave the plan.",
            "Complaints About the Health Plan": "Number of complaints filed about the plan."
        },
        "Appeals": {
            "Timeliness of Appeals Decisions": "Time taken to resolve member appeals.",
            "Plan Makes Timely Decisions About Appeals": "Adherence to decision timelines."
        }
    }
}

# === 2. Baseline values logic (1–5 scale) ===
def baseline_kpis():
    flat = {}
    for groups in categorized_kpis.values():
        for items in groups.values():
            for kpi in items.keys():
                if "Complaints" in kpi or "Problems" in kpi:
                    flat[kpi] = 1.0           # worst
                elif "Rating" in kpi or "Adherence" in kpi:
                    flat[kpi] = 3.0           # mid
                elif "Accuracy" in kpi or "Timeliness" in kpi:
                    flat[kpi] = 4.0           # good
                else:
                    flat[kpi] = 2.0           # below mid
    return flat

# === 3. Recommendations map ===
kpi_recommendations = {
    "Medication Adherence - Diabetes": "Invest in pharmacy outreach and digital refill reminders to improve medication adherence.",
    "Customer Service Rating": "Enhance call center training and reduce wait times to improve member satisfaction.",
    "Timeliness of Appeals Decisions": "Automate case handling workflows to accelerate resolution and ensure compliance.",
    "Plan Makes Timely Decisions About Appeals": "Implement SLA dashboards and audit queues to reduce delays in decisions.",
    "Getting Appointments and Care Quickly": "Expand provider network or offer telehealth to improve timely access."
}

# === 4. STAR score calculation (normalized to new range) ===
BASE_SCORE = 3.2

def calculate_star_score(kpis: dict) -> float:
    total = sum(kpis.values())
    n = len(kpis)
    min_sum = n * 1.0
    max_sum = n * 5.0
    ratio = (total - min_sum) / (max_sum - min_sum)
    ratio = max(0.0, min(1.0, ratio))
    return BASE_SCORE + ratio * (5 - BASE_SCORE)

# === 5. Generate top-5 “AI” recommendations ===
def generate_recommendations(kpis: dict) -> list[str]:
    low = sorted(
        ((k, v) for k, v in kpis.items() if v < 3.0),
        key=lambda kv: kv[1]
    )[:5]
    recs = []
    for kpi, val in low:
        advice = kpi_recommendations.get(kpi, "Focus operational improvements on this area.")
        recs.append(f"📉 \"{kpi}\" (score: {val}) – {advice}")
    return recs

# === 6. Streamlit app ===

# Initialize session state
if "kpis" not in st.session_state:
    st.session_state.kpis = baseline_kpis()

# Reset button
if st.button("🔄 Reset to Baseline"):
    st.session_state.kpis = baseline_kpis()
    st.experimental_rerun()

# Display current STAR rating
st.markdown(
    f"**Projected STAR Rating:** {calculate_star_score(st.session_state.kpis):.2f}"
)

# Sliders inside expanders (1–5)
for domain, groups in categorized_kpis.items():
    with st.expander(domain):
        for subgroup, items in groups.items():
            st.markdown(f"**{subgroup}**")
            for label in items.keys():
                new_val = st.slider(
                    label=label,
                    min_value=1.0,
                    max_value=5.0,
                    value=float(st.session_state.kpis[label]),
                    step=1.0,
                    key=label
                )
                st.session_state.kpis[label] = new_val

# Prepare DataFrame for charts
df = (
    pd.DataFrame.from_dict(st.session_state.kpis, orient="index", columns=["value"])
      .reset_index()
      .rename(columns={"index": "KPI"})
)

# Tabs for Radar vs. Bar
tab1, tab2 = st.tabs(["Radar View", "Bar View"])

with tab1:
    fig = px.line_polar(
        df,
        r="value",
        theta="KPI",
        line_close=True,
        title="KPI Impact (Radar)"
    )
    st.plotly_chart(fig, use_container_width=True, height=500)

with tab2:
    fig = px.bar(
        df,
        x="value",
        y="KPI",
        orientation="h",
        title="KPI Impact (Bar)"
    )
    st.plotly_chart(fig, use_container_width=True, height=500)

# AI Recommendations
st.markdown("### AI Recommendations")
for rec in generate_recommendations(st.session_state.kpis):
    st.write(rec)
