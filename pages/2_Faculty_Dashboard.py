import streamlit as st
import pandas as pd
from datetime import datetime

from core.auth import role_guard, logout_button
from core.theme import apply_theme
from core.utils import (
    date_range_picker, join_case_titles, sort_by_timestamp, is_empty, to_float
)
from core.components import (
    section_header, kpi_row, kpi_card,
    plot_line, plot_bar, plot_heatmap, show_empty
)

# QUERY IMPORTS
from core.queries.attempts_queries import load_attempts
from core.queries.engagement_queries import load_engagement_logs
from core.queries.rubric_queries import load_rubric_case_dimension_matrix
from core.queries.meta_queries import load_case_metadata # For case titles

from core.queries.admin_queries import ( 
    case_study_summary,
    campus_summary,
    department_summary
)


# --------------------------- PAGE SETUP ---------------------------

apply_theme()
# Enforce Faculty role
user_role, username = role_guard("Faculty") 

st.title("🏫 Faculty Dashboard")
st.caption(f"Welcome, **{username}**")
logout_button()

st.markdown("---")

# --------------------------- DATE FILTER ---------------------------

# Returns date strings ('YYYY-MM-DD') or None
start_date, end_date = date_range_picker()
if not start_date or not end_date:
    st.stop()


# --------------------------- LOAD DATA ---------------------------

@st.cache_data(ttl=3600)
def get_metadata():
    """Load static case metadata."""
    return load_case_metadata()

case_metadata_df = get_metadata()

# Core Data: Attempts, Engagement, Rubric Matrix, Case Summary (ALL FILTERED by date)
attempts_df = load_attempts(start_date, end_date)
attempts_df = to_float(attempts_df, "score")
attempts_df = to_float(attempts_df, "duration_seconds")
attempts_df = join_case_titles(attempts_df, case_metadata_df)

eng_df = load_engagement_logs(start_date, end_date)

# FILTERED Rubric Matrix
rubric_matrix = load_rubric_case_dimension_matrix(start_date, end_date) 
rubric_matrix = join_case_titles(rubric_matrix, case_metadata_df)

# FILTERED Case Summary
case_summary = case_study_summary(start_date, end_date)
case_summary = join_case_titles(case_summary, case_metadata_df)


# --------------------------- VALIDATION ---------------------------

if is_empty(attempts_df):
    st.warning("No student attempts found for the selected date range. Please widen your date filter.")
    st.stop()

# --------------------------- KPI SECTION ---------------------------

section_header("Class Performance Overview")

avg_score = attempts_df["score"].mean().round(2)
attempt_1 = attempts_df[attempts_df["attempt_number"] == 1]["score"].mean()
attempt_2 = attempts_df[attempts_df["attempt_number"] == 2]["score"].mean()

# Calculate improvement as delta
improvement = None
if pd.notna(attempt_1) and pd.notna(attempt_2):
    improvement = round(attempt_2 - attempt_1, 2)

active_students = attempts_df["student_id"].nunique()

avg_ces = attempts_df["ces_value"].mean()
avg_time_minutes = (attempts_df["duration_seconds"].mean() / 60).round(1)

# KPI Row updated to use delta for improvement
kpi_row([
    ("Active Students", active_students, None),
    ("Average Class Score", avg_score, improvement),
    ("Avg Time on Task (mins)", avg_time_minutes, None),
    ("Average CES Score", round(avg_ces, 2), None),
])


# --------------------------- SCORE DISTRIBUTION ---------------------------

section_header("📊 Score Distribution by Case Study")

# Group by the clean 'title' instead of 'case_id'
if not is_empty(attempts_df):
    plot_bar(
        attempts_df.groupby("title")["score"].mean().reset_index(),
        x="title",
        y="score",
        title="Average Score per Case Study"
    )
else:
    show_empty()

# --------------------------- IMPROVEMENT ---------------------------

section_header("Attempt 1 → Attempt 2 Improvement (by Case)")

if "attempt_number" in attempts_df.columns:
    # Pivot by case title for better readability
    compare = attempts_df.pivot_table(
        index="title", 
        columns="attempt_number", 
        values="score", 
        aggfunc="mean"
    ).reset_index()

    # Calculate improvement column safely
    if 1 in compare.columns and 2 in compare.columns:
        compare["improvement"] = (compare[2] - compare[1]).round(2)
        
        # Filter out cases with no second attempt score
        plot_df = compare.dropna(subset=[1, 2]).sort_values(by="improvement", ascending=False)
        
        if not is_empty(plot_df):
            plot_bar(plot_df, x="title", y="improvement", title="Score Improvement by Case (Attempt 2 - Attempt 1)")
        else:
            show_empty("Not enough attempts to compare scores between Attempt 1 and 2.")
    else:
        show_empty("Data for both Attempt 1 and Attempt 2 are required for this comparison.")
else:
    show_empty()

# --------------------------- RUBRIC MASTERY HEATMAP ---------------------------

section_header("Rubric Mastery Heatmap: Case vs Dimension")

if not is_empty(rubric_matrix):
    
    # Use the custom heatmap component
    plot_heatmap(
        rubric_matrix,
        index="rubric_dimension",
        columns="title", # Use title instead of case_id
        values="mastery",
        title="Average Mastery Rate Across Dimensions and Cases"
    )
else:
    show_empty("No rubric score data available for the selected range.")

# --------------------------- ENGAGEMENT TREND ---------------------------

section_header("📅 Engagement Over Time")

if not is_empty(eng_df):
    eng_plot = eng_df.copy()
    eng_plot = sort_by_timestamp(eng_plot, column="timestamp")
    
    # Group by day and count session IDs
    timeline = eng_plot.groupby(eng_plot["timestamp"].dt.date)["session_id"].count().reset_index().rename(
        columns={"timestamp": "day", "session_id": "events"}
    )
    plot_line(timeline, x="day", y="events", title="Daily Engagement Events")
else:
    show_empty("No engagement events found for the selected date range.")

# --------------------------- CASE SUMMARY TABLE ---------------------------

section_header("📚 Case Study Summary (Filtered)")

if not is_empty(case_summary):
    # Select columns to display
    display_cols = ["title", "total_attempts", "total_students", "avg_score", "avg_duration_sec"]
    st.dataframe(case_summary[display_cols].rename(columns={"title": "Case Study Title"}), use_container_width=True)
else:
    show_empty()

# --------------------------- CAMPUS/DEPARTMENT SUMMARY ---------------------------

cols = st.columns(2)

with cols[0]:
    section_header("Global Campus Summary")
    # Called without date filter as these are assumed to be static/global aggregates
    campus_df = campus_summary() 
    if not is_empty(campus_df):
        st.dataframe(campus_df, use_container_width=True)
    else:
        show_empty()

with cols[1]:
    section_header("Global Department Summary")
    # Called without date filter as these are assumed to be static/global aggregates
    dept_df = department_summary()
    if not is_empty(dept_df):
        st.dataframe(dept_df, use_container_width=True)
    else:
        show_empty()
