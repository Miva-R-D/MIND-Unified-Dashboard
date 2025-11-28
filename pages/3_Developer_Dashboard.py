import streamlit as st
import pandas as pd
from core.auth import role_guard, logout_button
from core.theme import apply_theme
from core.utils import date_range_picker, is_empty, to_float
from core.components import (
    section_header, kpi_card, kpi_row,
    plot_line, plot_bar, plot_hist, plot_scatter, show_empty
)

# QUERY IMPORTS
from core.queries.reliability_queries import (
    load_system_reliability,
    load_api_latency_summary,
    load_error_rate_by_api,
    load_critical_incidents,
    load_incidents_by_location,
    load_latest_reliability
)

from core.queries.environment_queries import (
    load_environment_with_attempts,
    load_device_type_distribution
)

# --------------------------- PAGE SETUP ---------------------------

apply_theme()
user_role, username = role_guard("Developer")

st.title("🛠️ Developer Dashboard")
st.caption(f"Welcome, **{username}** — System Reliability & Environment Insights")
logout_button()

st.markdown("---")


# --------------------------- DATE FILTER ---------------------------

start_date, end_date = date_range_picker()
if not start_date or not end_date:
    st.stop()


# --------------------------- LOAD SYSTEM RELIABILITY ---------------------------

# Time-series trend data
rel_df = load_system_reliability(start_date, end_date)

# Aggregate/Summary data (now filtered by date)
api_latency = load_api_latency_summary(start_date, end_date)
error_rates = load_error_rate_by_api(start_date, end_date)
critical_inc = load_critical_incidents(start_date, end_date)
incidents_by_loc = load_incidents_by_location(start_date, end_date)
device_mix = load_device_type_distribution(start_date, end_date)


# Environment + attempts (filtered)
env_attempts = load_environment_with_attempts(start_date, end_date)
env_attempts = to_float(env_attempts, "score") # Ensure score is float for correlation plot
env_attempts = to_float(env_attempts, "internet_latency_ms")


# Latest Snapshot (no date filter, gets the very latest entry)
latest_rel = load_latest_reliability()


# --------------------------- KPI SECTION ---------------------------

section_header("System Reliability Snapshot")

if not is_empty(latest_rel):
    # Ensure latest_rel has numeric columns for aggregation
    latest_rel = to_float(latest_rel, "reliability_index")
    latest_rel = to_float(latest_rel, "latency_ms")
    latest_rel = to_float(latest_rel, "error_rate")
    
    # KPIs based on the latest available single reading (or small window)
    avg_rel = latest_rel["reliability_index"].mean().round(2)
    avg_latency = latest_rel["latency_ms"].mean().round(2)
    avg_error = latest_rel["error_rate"].mean().round(4)
    
    # NOTE: In a production environment, reliability KPIs should use P95/P99 latency
    # The current query structure doesn't support that easily, so we stick to AVG
    kpi_row([
        ("Avg Reliability Index (recent)", avg_rel, None),
        ("Avg Latency (ms) (recent)", avg_latency, None),
        ("Avg Error Rate (recent)", avg_error, None),
    ])
else:
    show_empty("No recent reliability metrics found.")


# --------------------------- API LATENCY ---------------------------

section_header("⏱️ API Latency Overview (P95)")

if not is_empty(api_latency):
    api_latency = to_float(api_latency, "p95_latency") # Assuming p95_latency is now present
    
    plot_bar(
        api_latency.sort_values(by="p95_latency", ascending=False), 
        x="api_name", 
        y="p95_latency", 
        title=f"P95 Latency (ms) per API ({start_date} to {end_date})"
    )
else:
    show_empty("No API latency data found for the selected period.")


# --------------------------- ERROR RATES ---------------------------

section_header("🚨 Error Rate by API")

if not is_empty(error_rates):
    error_rates = to_float(error_rates, "avg_error")
    
    plot_bar(
        error_rates.sort_values(by="avg_error", ascending=False), 
        x="api_name", 
        y="avg_error", 
        title=f"Average Error Rate per API ({start_date} to {end_date})"
    )
else:
    show_empty("No API error rate data found for the selected period.")


# --------------------------- RELIABILITY TREND ---------------------------

section_header("📉 Reliability Index Trend")

if not is_empty(rel_df):
    rel_df = to_float(rel_df, "reliability_index")
    
    plot_line(
        rel_df, 
        x="timestamp", 
        y="reliability_index", 
        title="Reliability Index Over Time"
    )
else:
    show_empty("No historical reliability data found for the selected period.")


# --------------------------- CRITICAL INCIDENTS ---------------------------

section_header("⚠️ Critical Incidents")

if not is_empty(critical_inc):
    st.dataframe(critical_inc, use_container_width=True)
else:
    show_empty("No critical incidents recorded in the selected period.")


# --------------------------- INCIDENTS BY LOCATION ---------------------------

section_header("📍 Incidents by Location")

if not is_empty(incidents_by_loc):
    incidents_by_loc = to_float(incidents_by_loc, "incidents")
    
    plot_bar(
        incidents_by_loc.sort_values(by="incidents", ascending=False), 
        x="location", 
        y="incidents", 
        title="Critical Incidents by Geographic Location"
    )
else:
    show_empty("No incident location data available.")


# --------------------------- ENVIRONMENT QUALITY ---------------------------

section_header("🌐 Environment Quality Correlations")

if not is_empty(env_attempts):
    st.markdown("Exploring the relationship between environmental factors and student performance (Score).")
    
    cols = st.columns(3)
    
    with cols[0]:
        plot_scatter(
            env_attempts, 
            x="internet_latency_ms", 
            y="score", 
            title="Internet Latency vs Score"
        )
    with cols[1]:
        plot_scatter(
            env_attempts, 
            x="internet_stability_score", 
            y="score", 
            title="Internet Stability vs Score"
        )
    with cols[2]:
        plot_scatter(
            env_attempts, 
            x="noise_level", 
            y="score", 
            title="Noise Level vs Score"
        )
else:
    show_empty("No combined environment and attempts data found for correlation analysis.")


# --------------------------- DEVICE TYPE DISTRIBUTION ---------------------------

section_header("📱 Device Type Distribution")

if not is_empty(device_mix):
    device_mix = to_float(device_mix, "count")
    
    plot_bar(
        device_mix, 
        x="device_type", 
        y="count", 
        title="Student Device Type Breakdown"
    )
else:
    show_empty("No device distribution data found.")
