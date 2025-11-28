import streamlit as st
import pandas as pd
from datetime import datetime

from core.auth import role_guard, logout_button
from core.theme import apply_theme
from core.utils import (
    date_range_picker, join_case_titles, sort_by_timestamp, 
    is_empty, to_float
)
from core.components import (
    section_header, kpi_row,
    plot_line, plot_bar, plot_hist, plot_scatter, show_empty
)

# QUERY IMPORTS
from core.queries.attempts_queries import (
    load_attempts_for_student,
    load_latest_attempts_per_case
)
from core.queries.engagement_queries import load_engagement_for_student
from core.queries.environment_queries import load_environment_for_student
from core.queries.rubric_queries import load_rubric_scores_for_student
from core.queries.meta_queries import load_case_metadata # NEW IMPORT

# --------------------------- PAGE SETUP ---------------------------

apply_theme()
# Check authentication and enforce Student role
user_role, username = role_guard("Student") 

st.title("🎓 Student Dashboard")
st.caption(f"Welcome, **{username}**")

logout_button()

st.markdown("---")


# --------------------------- DATE FILTER ---------------------------

# Returns date strings ('YYYY-MM-DD') or None
start_date, end_date = date_range_picker() 
if not start_date or not end_date:
    st.stop()


# --------------------------- LOAD DATA ---------------------------

# Use st.cache_data for static or expensive-to-load reference data
@st.cache_data(ttl=3600)
def get_metadata():
    """Load case metadata once and cache it."""
    return load_case_metadata()

case_metadata_df = get_metadata()

# Attempts (Core Data) - Filtered by date
attempts_df = load_attempts_for_student(username, start_date, end_date)
# Apply necessary casting and join title
attempts_df = to_float(attempts_df, "score")
attempts_df = to_float(attempts_df, "duration_seconds")
attempts_df = join_case_titles(attempts_df, case_metadata_df)


# Engagement - Filtered by date
eng_df = load_engagement_for_student(username, start_date, end_date)

# Environment - Filtered by date
env_df = load_environment_for_student(username, start_date, end_date) # ADDED DATE FILTER

# Latest attempt per case (for KPIs) - Unfiltered by date for true latest state
latest_attempts = load_latest_attempts_per_case(username) 
latest_attempts = to_float(latest_attempts, "score")

# Rubric - Filtered by date
rubric_df = load_rubric_scores_for_student(username, start_date, end_date) # ADDED DATE FILTER
rubric_df = join_case_titles(rubric_df, case_metadata_df)


# --------------------------- VALIDATION ---------------------------

if is_empty(attempts_df):
    st.warning("No attempts found for the selected date range.")
    show_empty("Try selecting a wider date range.")
    st.stop()

# --------------------------- KPI SECTION ---------------------------

section_header("🎯 Your Learning Summary")

total_cases = attempts_df["case_id"].nunique()
total_attempts = len(attempts_df)
avg_score = latest_attempts["score"].mean().round(2)
avg_ces = attempts_df["ces_value"].mean().round(2) if "ces_value" in attempts_df else 0.0
# Convert avg_time to minutes for cleaner display
avg_time_seconds = attempts_df["duration_seconds"].mean()
avg_time_minutes = (avg_time_seconds / 60).round(1)

kpi_row([
    ("Total Attempts", total_attempts, None),
    ("Average Latest Score", f"{avg_score}%", None),
    ("Average Time on Task (mins)", f"{avg_time_minutes}", None),
    ("Average CES", avg_ces, None),
])

# --------------------------- SCORE TREND ---------------------------

section_header("📈 Score Trend Over Time")

# Sort data and plot line graph
attempts_df_sorted = sort_by_timestamp(attempts_df, column="timestamp")

if not is_empty(attempts_df_sorted):
    # Plotting score, using case title for color/line grouping
    plot_line(
        attempts_df_sorted, 
        x="timestamp", 
        y="score", 
        color="title", 
        title="Score Trend Across All Attempts"
    )
else:
    show_empty("No score data to plot.")

# --------------------------- FIRST VS SECOND ATTEMPT ---------------------------

section_header("Attempt 1 vs Attempt 2 (By Case)")

if "attempt_number" in attempts_df.columns:
    # Group by case title and attempt number, then take the average score
    attempt_compare = attempts_df.groupby(["title", "attempt_number"])["score"].mean().reset_index()
    
    # Filter only for the first two attempts (if available)
    attempt_compare = attempt_compare[attempt_compare["attempt_number"].isin([1, 2])]
    
    if not is_empty(attempt_compare):
        plot_bar(
            attempt_compare, 
            x="title", 
            y="score", 
            color="attempt_number", 
            title="Average Score: Attempt 1 vs Attempt 2 by Case"
        )
    else:
        show_empty("Only one attempt per case found, comparison not available.")
else:
    show_empty()

# --------------------------- RUBRIC DIMENSIONS ---------------------------

section_header("📊 Rubric Dimension Breakdown")

if not is_empty(rubric_df):
    # Calculate mastery rate (score/max_score)
    rubric_df["mastery_rate"] = rubric_df["score"] / rubric_df["max_score"]
    
    # Aggregate mastery by dimension
    rubric_agg = rubric_df.groupby("rubric_dimension")["mastery_rate"].mean().reset_index()
    
    plot_bar(
        rubric_agg, 
        x="rubric_dimension", 
        y="mastery_rate", 
        title="Average Mastery Rate by Rubric Dimension"
    )
else:
    show_empty("No rubric scores found for the selected period.")

# --------------------------- TIME ON TASK VS SCORE ---------------------------

section_header("⏱️ Correlation: Duration vs Score")

if "duration_seconds" in attempts_df.columns and "score" in attempts_df.columns:
    plot_scatter(
        attempts_df, 
        x="duration_seconds", 
        y="score", 
        color="title", 
        title="Attempt Duration vs Final Score"
    )
else:
    show_empty()

# --------------------------- CES DISTRIBUTION ---------------------------

section_header("😊 CES Score Distribution")

if "ces_value" in attempts_df.columns:
    plot_hist(
        attempts_df, 
        x="ces_value", 
        title="Customer Effort Score (CES) Distribution"
    )
else:
    show_empty("CES data not available in attempts.")


# --------------------------- ENGAGEMENT TIMELINE ---------------------------

section_header("📅 Engagement Over Time")

if not is_empty(eng_df):
    eng_daily = eng_df.copy()
    
    # Ensure timestamp is datetime type for .dt.date access
    eng_daily = sort_by_timestamp(eng_daily, column="timestamp") 
    
    # Group by day and count session IDs
    timeline = eng_daily.groupby(eng_daily["timestamp"].dt.date)["session_id"].count().reset_index().rename(
        columns={"timestamp": "day", "session_id": "events"}
    )
    plot_line(timeline, x="day", y="events", title="Daily Engagement Events")
else:
    show_empty("No engagement events found for the selected date range.")


# --------------------------- ENVIRONMENT SNAPSHOT ---------------------------

section_header("🖥️ Environment Snapshot (Latest Readings)")

if not is_empty(env_df):
    st.markdown("Metrics recorded at the time of your attempts:")
    
    # Select key environment metrics for display and join with attempts for context
    env_display = env_df.merge(
        attempts_df[["attempt_id", "timestamp", "score", "title"]], 
        on="attempt_id", 
        how="left"
    ).sort_values(by="timestamp", ascending=False).head(5)
    
    st.dataframe(
        env_display[[
            "timestamp", "title", "score", "internet_latency_ms", 
            "noise_level", "device_type"
        ]].set_index("timestamp")
    )
else:
    show_empty("No environment data found for your recent attempts.")
