import streamlit as st

from core.auth import role_guard, logout_button
from core.theme import apply_theme
from core.utils import (
    date_range_picker, join_case_titles, sort_by_timestamp, is_empty
)
from core.components import (
    section_header, kpi_row, kpi_card,
    plot_line, plot_bar, plot_scatter, plot_hist, show_empty
)

from core.queries.attempts_queries import load_attempts
from core.queries.engagement_queries import load_engagement_logs
from core.queries.rubric_queries import (
    load_rubric_case_dimension_matrix
)

from core.queries.admin_queries import (
    load_admin_aggregates, case_study_summary,
    campus_summary, department_summary
)

from core.db import run_query

apply_theme()
user_role, username = role_guard("Faculty")

st.title("🏫 Faculty Dashboard")
st.caption(f"Welcome, **{username}**")
logout_button()

st.markdown("---")

# --------------------------- DATE FILTER ---------------------------

start_date, end_date = date_range_picker()
if not start_date or not end_date:
    st.stop()

# --------------------------- LOAD DATA ---------------------------

attempts_df = load_attempts(start_date, end_date)
eng_df = load_engagement_logs(start_date, end_date)
rubric_matrix = load_rubric_case_dimension_matrix()
case_summary = case_study_summary()

# --------------------------- VALIDATION ---------------------------

if is_empty(attempts_df):
    st.warning("No attempts found for the selected date range.")
    st.stop()

# --------------------------- KPI SECTION ---------------------------

section_header("Class Performance Overview")

avg_score = attempts_df["score"].mean().round(2)
attempt_1 = attempts_df[attempts_df["attempt_number"] == 1]["score"].mean()
attempt_2 = attempts_df[attempts_df["attempt_number"] == 2]["score"].mean()

improvement = None
if attempt_1 and attempt_2:
    improvement = round(attempt_2 - attempt_1, 2)

active_students = attempts_df["student_id"].nunique()
completion_rate = (
    attempts_df["student_id"].nunique() / attempts_df["case_id"].nunique()
) * 100

avg_ces = attempts_df["ces_value"].mean()
avg_time = attempts_df["duration_seconds"].mean()

kpi_row([
    ("Active Students", active_students),
    ("Average Class Score", avg_score),
    ("Avg Time on Task (secs)", round(avg_time, 2)),
    ("Average CES Score", round(avg_ces, 2)),
])

if improvement:
    kpi_card("Avg Attempt Improvement", improvement)

# --------------------------- SCORE DISTRIBUTION ---------------------------

section_header("📊 Score Distribution by Case Study")

if not is_empty(attempts_df):
    plot_bar(
        attempts_df.groupby("case_id")["score"].mean().reset_index(),
        x="case_id",
        y="score",
        title="Avg Score per Case"
    )
else:
    show_empty()

# --------------------------- IMPROVEMENT ---------------------------

section_header("Attempt 1 → Attempt 2 Improvement")

if "attempt_number" in attempts_df:
    compare = attempts_df.pivot_table(
        index="case_id",
        columns="attempt_number",
        values="score",
        aggfunc="mean"
    ).reset_index()

    if 1 in compare and 2 in compare:
        compare["improvement"] = compare[2] - compare[1]
        plot_bar(compare, x="case_id", y="improvement", title="Improvement by Case")
    else:
        show_empty()
else:
    show_empty()

# --------------------------- RUBRIC MASTERY HEATMAP ---------------------------

section_header("Rubric Mastery Heatmap")

if not is_empty(rubric_matrix):
    import plotly.express as px
    fig = px.imshow(
        rubric_matrix.pivot(
            index="rubric_dimension",
            columns="case_id",
            values="mastery"
        ),
        color_continuous_scale="Blues",
        aspect="auto",
        title="Rubric Mastery Matrix"
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    show_empty()

# --------------------------- ENGAGEMENT TREND ---------------------------

section_header("📅 Engagement Over Time")

if not is_empty(eng_df):
    eng_plot = eng_df.copy()
    eng_plot["day"] = eng_plot["timestamp"].dt.date
    timeline = eng_plot.groupby("day")["session_id"].count().reset_index().rename(
        columns={"session_id": "events"}
    )
    plot_line(timeline, x="day", y="events", title="Daily Engagement Events")
else:
    show_empty()

# --------------------------- CASE SUMMARY TABLE ---------------------------

section_header("📚 Case Study Summary")

if not is_empty(case_summary):
    st.dataframe(case_summary)
else:
    show_empty()

# --------------------------- CAMPUS/DEPARTMENT SUMMARY ---------------------------

cols = st.columns(2)

with cols[0]:
    section_header("Campus Summary")
    campus_df = campus_summary()
    if not is_empty(campus_df):
        st.dataframe(campus_df)
    else:
        show_empty()

with cols[1]:
    section_header("Department Summary")
    dept_df = department_summary()
    if not is_empty(dept_df):
        st.dataframe(dept_df)
    else:
        show_empty()

