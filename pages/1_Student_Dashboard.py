import streamlit as st
from datetime import datetime

from core.auth import role_guard, logout_button
from core.theme import apply_theme
from core.utils import date_range_picker, join_case_titles, sort_by_timestamp, is_empty
from core.components import (
    section_header, kpi_card, kpi_row,
    plot_line, plot_bar, plot_hist, plot_scatter, show_empty
)

from core.queries.attempts_queries import (
    load_attempts_for_student,
    load_latest_attempts_per_case
)

from core.queries.engagement_queries import (
    load_engagement_for_student
)

from core.queries.environment_queries import (
    load_environment_for_student
)

from core.queries.rubric_queries import (
    load_rubric_scores_for_student
)

from core.db import run_query


# --------------------------- PAGE SETUP ---------------------------

apply_theme()
user_role, username = role_guard("Student")

st.title("🎓 Student Dashboard")
st.caption(f"Welcome, **{username}**")

logout_button()

st.markdown("---")


# --------------------------- DATE FILTER ---------------------------

start_date, end_date = date_range_picker()
if not start_date or not end_date:
    st.stop()


# --------------------------- LOAD DATA ---------------------------

# Attempts
attempts_df = load_attempts_for_student(username, start_date, end_date)

# Engagement
eng_df = load_engagement_for_student(username, start_date, end_date)

# Environment
env_df = load_environment_for_student(username)

# Latest attempt per case (for KPIs)
latest_attempts = load_latest_attempts_per_case(username)

# Rubric
rubric_df = load_rubric_scores_for_student(username)


# --------------------------- VALIDATION ---------------------------

if is_empty(attempts_df):
    st.warning("No attempts found for the selected date range.")
    st.stop()


# --------------------------- KPI SECTION ---------------------------

section_header("Your Learning Summary")

total_cases = attempts_df["case_id"].nunique()
completion_rate = (total_cases / total_cases) * 100 if total_cases > 0 else 0  # proxy
avg_score = latest_attempts["score"].mean().round(2)
avg_ces = attempts_df["ces_value"].mean().round(2) if "ces_value" in attempts_df else None
avg_time = attempts_df["duration_seconds"].mean().round(2)

kpi_row([
    ("Total Case Studies Attempted", total_cases),
    ("Average Score", avg_score),
    ("Average Time on Task (secs)", avg_time),
    ("Average CES", avg_ces),
])


# --------------------------- SCORE TREND ---------------------------

section_header("📈 Score Trend Over Time")

attempts_df = sort_by_timestamp(attempts_df)

if not is_empty(attempts_df):
    plot_line(attempts_df, x="timestamp", y="score", title="Score over Time")
else:
    show_empty()


# --------------------------- FIRST VS SECOND ATTEMPT ---------------------------

section_header("Attempt 1 vs Attempt 2")

if "attempt_number" in attempts_df:
    attempt_compare = attempts_df.groupby("attempt_number")["score"].mean().reset_index()
    plot_bar(attempt_compare, x="attempt_number", y="score", title="Attempt Comparison")
else:
    show_empty()


# --------------------------- RUBRIC DIMENSIONS ---------------------------

section_header("Rubric Dimension Breakdown")

if not is_empty(rubric_df):
    rubric_df["mastery"] = rubric_df["score"] / rubric_df["max_score"]
    rubric_agg = rubric_df.groupby("rubric_dimension")["mastery"].mean().reset_index()
    plot_bar(rubric_agg, x="rubric_dimension", y="mastery", title="Mastery by Dimension")
else:
    show_empty()


# --------------------------- TIME ON TASK VS SCORE ---------------------------

section_header("⏱️ Time on Task vs Score")

if "duration_seconds" in attempts_df:
    plot_scatter(attempts_df, x="duration_seconds", y="score", title="Time vs Score")
else:
    show_empty()


# --------------------------- CES DISTRIBUTION ---------------------------

section_header("CES Score Distribution")

if "ces_value" in attempts_df:
    plot_hist(attempts_df, x="ces_value", title="CES Distribution")
else:
    show_empty()


# --------------------------- ENGAGEMENT TIMELINE ---------------------------

section_header("📅 Engagement Over Time")

if not is_empty(eng_df):
    eng_daily = eng_df.copy()
    eng_daily["day"] = eng_daily["timestamp"].dt.date
    timeline = eng_daily.groupby("day")["session_id"].count().reset_index().rename(
        columns={"session_id": "events"}
    )
    plot_line(timeline, x="day", y="events", title="Engagement Events per Day")
else:
    show_empty()


# --------------------------- ENVIRONMENT SNAPSHOT ---------------------------

section_header("🖥️ Environment Snapshot")

if not is_empty(env_df):
    st.dataframe(env_df)
else:
    show_empty()

