"""
Faculty Dashboard - Cohort Performance Analytics
Monitor student performance, identify at-risk students, analyze rubric mastery
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from auth import require_auth, get_current_user
from theme import apply_streamlit_theme, COLORS
from db import get_db_manager
from core.components import (
    render_kpi_card, render_metric_grid, create_line_chart, create_bar_chart,
    create_heatmap, create_box_plot, render_data_table
)
from core.utils import (
    format_number, format_percentage, format_duration, get_date_range_filter,
    get_at_risk_students
)
from core.queries.attempts_queries import (
    get_cohort_performance, get_attempt_improvement, 
    get_attempt_statistics_by_case, get_completion_rate_by_case
)
from core.queries.rubric_queries import (
    get_cohort_rubric_performance
)
from core.queries.engagement_queries import (
    get_cohort_engagement_summary, get_daily_engagement_trend
)

# Page config
st.set_page_config(
    page_title="Faculty Dashboard - MIND",
    page_icon="👩‍🏫",
    layout="wide"
)

# Apply theme
st.markdown(apply_streamlit_theme(), unsafe_allow_html=True)

# Require authentication
require_auth(allowed_roles=["Faculty", "Admin"])

# Get user info
user = get_current_user()

# Initialize database
db = get_db_manager()

# Header
st.markdown("# 👩‍🏫 Faculty Dashboard")
st.markdown(f"### Welcome, {user['name']}!")
st.markdown("Monitor student performance, identify at-risk learners, and analyze cohort trends")
st.markdown("---")

# ============================================================================
# FILTERS SECTION
# ============================================================================

st.markdown("### 📊 Filters")

col1, col2, col3, col4 = st.columns(4)

with col1:
    # Get available cohorts
    cohorts_query = "SELECT DISTINCT cohort_id FROM students WHERE cohort_id IS NOT NULL ORDER BY cohort_id"
    cohorts_df = db.execute_query_df(cohorts_query)
    cohort_options = ['All'] + cohorts_df['cohort_id'].tolist() if not cohorts_df.empty else ['All']
    selected_cohort = st.selectbox("Cohort", cohort_options)

with col2:
    # Get available departments
    dept_query = "SELECT DISTINCT department FROM students WHERE department IS NOT NULL ORDER BY department"
    dept_df = db.execute_query_df(dept_query)
    dept_options = ['All'] + dept_df['department'].tolist() if not dept_df.empty else ['All']
    selected_department = st.selectbox("Department", dept_options)

with col3:
    # Get available campuses
    campus_query = "SELECT DISTINCT campus FROM students WHERE campus IS NOT NULL ORDER BY campus"
    campus_df = db.execute_query_df(campus_query)
    campus_options = ['All'] + campus_df['campus'].tolist() if not campus_df.empty else ['All']
    selected_campus = st.selectbox("Campus", campus_options)

with col4:
    # Date range filter
    date_range = st.selectbox(
        "Time Period",
        ["Last 7 Days", "Last 30 Days", "Last 90 Days", "All Time", "Custom Range"]
    )

# Get date filter
date_range_map = {
    "Last 7 Days": 7,
    "Last 30 Days": 30,
    "Last 90 Days": 90,
    "All Time": 365,
    "Custom Range": 30
}

# Then call with the number:
if date_range != "Custom Range":
    days = date_range_map.get(date_range, 30)
    start_date = datetime.now() - timedelta(days=days)
    end_date = datetime.now()
    
start_date, end_date = get_date_range_filter(date_range)

# Custom date range
if date_range == "Custom Range":
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", value=datetime.now() - timedelta(days=30))
    with col2:
        end_date = st.date_input("End Date", value=datetime.now())

st.markdown("---")

# ============================================================================
# BUILD DYNAMIC FILTERS FOR QUERIES
# ============================================================================

def build_student_filter():
    """Build WHERE clause for student filtering"""
    conditions = ["s.role = 'Student'"]
    
    if selected_cohort != 'All':
        conditions.append(f"s.cohort_id = '{selected_cohort}'")
    if selected_department != 'All':
        conditions.append(f"s.department = '{selected_department}'")
    if selected_campus != 'All':
        conditions.append(f"s.campus = '{selected_campus}'")
    
    return " AND ".join(conditions)

def build_date_filter(alias='a'):
    """Build date filter for attempts"""
    if start_date and end_date:
        return f"{alias}.timestamp >= '{start_date}' AND {alias}.timestamp <= '{end_date}'"
    return "1=1"

# ============================================================================
# KEY PERFORMANCE INDICATORS
# ============================================================================

st.markdown("### 📈 Key Performance Indicators")

# Query for KPIs
student_filter = build_student_filter()
date_filter = build_date_filter()

kpi_query = f"""
WITH student_base AS (
    SELECT student_id
    FROM students s
    WHERE {student_filter}
),
student_attempts AS (
    SELECT 
        a.student_id,
        a.score,
        a.attempt_number,
        a.ces_value,
        a.duration_seconds,
        a.case_id
    FROM attempts a
    INNER JOIN student_base sb ON a.student_id = sb.student_id
    WHERE {date_filter}
),
student_stats AS (
    SELECT 
        COUNT(DISTINCT student_id) as total_students,
        AVG(score) as avg_score,
        COUNT(DISTINCT CASE WHEN attempt_number = 1 THEN student_id END) as students_attempted,
        AVG(ces_value) as avg_ces,
        AVG(duration_seconds) as avg_duration
    FROM student_attempts
),
improvement_stats AS (
    SELECT 
        AVG(CASE WHEN attempt_number = 2 THEN score END) - 
        AVG(CASE WHEN attempt_number = 1 THEN score END) as avg_improvement
    FROM student_attempts
),
at_risk_count AS (
    SELECT COUNT(DISTINCT student_id) as at_risk
    FROM student_attempts
    WHERE score < 60
)
SELECT 
    COALESCE(ss.total_students, 0) as total_students,
    COALESCE(ss.students_attempted, 0) as students_attempted,
    COALESCE(ss.avg_score, 0) as avg_score,
    COALESCE(ss.avg_ces, 0) as avg_ces,
    COALESCE(ss.avg_duration, 0) as avg_duration,
    COALESCE(i.avg_improvement, 0) as avg_improvement,
    COALESCE(ar.at_risk, 0) as at_risk
FROM student_stats ss
CROSS JOIN improvement_stats i
CROSS JOIN at_risk_count ar
"""

kpi_df = db.execute_query_df(kpi_query)

if not kpi_df.empty:
    kpi = kpi_df.iloc[0]
    
    # Safely get values
    total_students = int(kpi['total_students']) if pd.notna(kpi['total_students']) else 0
    students_attempted = int(kpi['students_attempted']) if pd.notna(kpi['students_attempted']) else 0
    avg_score = float(kpi['avg_score']) if pd.notna(kpi['avg_score']) else 0
    avg_ces = float(kpi['avg_ces']) if pd.notna(kpi['avg_ces']) else 0
    avg_duration = float(kpi['avg_duration']) if pd.notna(kpi['avg_duration']) else 0
    avg_improvement = float(kpi['avg_improvement']) if pd.notna(kpi['avg_improvement']) else 0
    at_risk = int(kpi['at_risk']) if pd.notna(kpi['at_risk']) else 0
    
    # Calculate completion rate
    completion_rate = (students_attempted / total_students * 100) if total_students > 0 else 0
    
    metrics = [
        {
            'title': 'Total Students',
            'value': total_students,
            'accent': False
        },
        {
            'title': 'Active Students',
            'value': students_attempted,
            'accent': False
        },
        {
            'title': 'Average Score',
            'value': f"{avg_score:.1f}%" if avg_score > 0 else "N/A",
            'accent': True
        },
        {
            'title': 'Avg Improvement',
            'value': f"+{avg_improvement:.1f}%" if avg_improvement > 0 else f"{avg_improvement:.1f}%" if avg_improvement != 0 else "N/A",
            'accent': True if avg_improvement > 0 else False
        },
        {
            'title': 'Completion Rate',
            'value': f"{completion_rate:.1f}%",
            'accent': False
        },
        {
            'title': 'Students At Risk',
            'value': at_risk,
            'accent': True if at_risk > 0 else False
        },
        {
            'title': 'Average CES',
            'value': f"{avg_ces:.1f}" if avg_ces > 0 else "N/A",
            'accent': False
        },
        {
            'title': 'Avg Time on Task',
            'value': format_duration(int(avg_duration)) if avg_duration > 0 else "N/A",
            'accent': False
        }
    ]
    
    render_metric_grid(metrics, columns=4)
else:
    st.info("📊 No data available for the selected filters")

st.markdown("---")

# ============================================================================
# CHARTS SECTION
# ============================================================================

st.markdown("### 📊 Performance Analytics")

# Two columns for charts
col1, col2 = st.columns(2)

with col1:
    st.markdown("#### 📈 Score Distribution by Case Study")
    
    # Query for score distribution
    score_dist_query = f"""
    SELECT 
        cs.title as case_title,
        AVG(a.score) as avg_score,
        MIN(a.score) as min_score,
        MAX(a.score) as max_score,
        COUNT(a.attempt_id) as attempt_count
    FROM attempts a
    INNER JOIN case_studies cs ON a.case_id = cs.case_id
    INNER JOIN students s ON a.student_id = s.student_id
    WHERE {student_filter}
    AND {date_filter}
    GROUP BY cs.case_id, cs.title
    ORDER BY cs.title
    """
    
    score_dist_df = db.execute_query_df(score_dist_query)
    
    if not score_dist_df.empty and len(score_dist_df) > 0:
        fig = create_bar_chart(
            score_dist_df,
            x='case_title',
            y='avg_score',
            title="Average Score by Case Study",
            xlabel="Case Study",
            ylabel="Average Score (%)"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data available for score distribution")

with col2:
    st.markdown("#### 🎯 Performance by Department")
    
    # Query for department performance
    dept_perf_query = f"""
    SELECT 
        s.department,
        AVG(a.score) as avg_score,
        COUNT(DISTINCT a.student_id) as student_count
    FROM attempts a
    INNER JOIN students s ON a.student_id = s.student_id
    WHERE {student_filter}
    AND {date_filter}
    AND s.department IS NOT NULL
    GROUP BY s.department
    ORDER BY avg_score DESC
    """
    
    dept_perf_df = db.execute_query_df(dept_perf_query)
    
    if not dept_perf_df.empty and len(dept_perf_df) > 0:
        fig = create_bar_chart(
            dept_perf_df,
            x='department',
            y='avg_score',
            title="Average Score by Department",
            xlabel="Department",
            ylabel="Average Score (%)",
            color_column='avg_score'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data available for department performance")

# Second row of charts
col3, col4 = st.columns(2)

with col3:
    st.markdown("#### 📊 Attempt 1 vs Attempt 2 Improvement")
    
    # Query for improvement
    improvement_query = f"""
    WITH attempt_scores AS (
        SELECT 
            a.case_id,
            cs.title as case_title,
            a.attempt_number,
            AVG(a.score) as avg_score
        FROM attempts a
        INNER JOIN case_studies cs ON a.case_id = cs.case_id
        INNER JOIN students s ON a.student_id = s.student_id
        WHERE {student_filter}
        AND {date_filter}
        AND a.attempt_number IN (1, 2)
        GROUP BY a.case_id, cs.title, a.attempt_number
    )
    SELECT 
        case_title,
        MAX(CASE WHEN attempt_number = 1 THEN avg_score END) as attempt_1,
        MAX(CASE WHEN attempt_number = 2 THEN avg_score END) as attempt_2
    FROM attempt_scores
    GROUP BY case_title
    HAVING MAX(CASE WHEN attempt_number = 1 THEN avg_score END) IS NOT NULL
    AND MAX(CASE WHEN attempt_number = 2 THEN avg_score END) IS NOT NULL
    ORDER BY case_title
    """
    
    improvement_df = db.execute_query_df(improvement_query)
    
    if not improvement_df.empty and len(improvement_df) > 0:
        # Calculate improvement
        improvement_df['improvement'] = improvement_df['attempt_2'] - improvement_df['attempt_1']
        
        fig = create_bar_chart(
            improvement_df,
            x='case_title',
            y='improvement',
            title="Average Improvement (Attempt 1 → 2)",
            xlabel="Case Study",
            ylabel="Improvement (%)",
            color_column='improvement'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data available for improvement tracking")

with col4:
    st.markdown("#### 🏆 Performance by Campus")
    
    # Query for campus performance
    campus_perf_query = f"""
    SELECT 
        s.campus,
        AVG(a.score) as avg_score,
        COUNT(DISTINCT a.student_id) as student_count
    FROM attempts a
    INNER JOIN students s ON a.student_id = s.student_id
    WHERE {student_filter}
    AND {date_filter}
    AND s.campus IS NOT NULL
    GROUP BY s.campus
    ORDER BY avg_score DESC
    """
    
    campus_perf_df = db.execute_query_df(campus_perf_query)
    
    if not campus_perf_df.empty and len(campus_perf_df) > 0:
        fig = create_bar_chart(
            campus_perf_df,
            x='campus',
            y='avg_score',
            title="Average Score by Campus",
            xlabel="Campus",
            ylabel="Average Score (%)",
            color_column='avg_score'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data available for campus performance")

st.markdown("---")

# ============================================================================
# RUBRIC MASTERY HEATMAP
# ============================================================================

st.markdown("### 🎯 Rubric Mastery Heatmap")

rubric_heatmap_query = f"""
SELECT 
    cs.title as case_title,
    rs.rubric_dimension,
    AVG(rs.score * 100.0 / NULLIF(rs.max_score, 0)) as avg_percentage
FROM rubric_scores rs
INNER JOIN attempts a ON rs.attempt_id = a.attempt_id
INNER JOIN case_studies cs ON a.case_id = cs.case_id
INNER JOIN students s ON a.student_id = s.student_id
WHERE {student_filter}
AND {date_filter}
GROUP BY cs.title, rs.rubric_dimension
ORDER BY cs.title, rs.rubric_dimension
"""

rubric_heatmap_df = db.execute_query_df(rubric_heatmap_query)

if not rubric_heatmap_df.empty and len(rubric_heatmap_df) > 0:
    # Pivot for heatmap
    heatmap_pivot = rubric_heatmap_df.pivot(
        index='rubric_dimension',
        columns='case_title',
        values='avg_percentage'
    )
    
    fig = create_heatmap(
        heatmap_pivot,
        title="Rubric Mastery by Case Study (%)",
        xlabel="Case Study",
        ylabel="Rubric Dimension"
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No rubric data available for the selected filters")

st.markdown("---")

# ============================================================================
# ENGAGEMENT TRENDS
# ============================================================================

st.markdown("### 📅 Engagement Trends Over Time")

engagement_trend_query = f"""
SELECT 
    DATE(el.timestamp) as date,
    COUNT(DISTINCT el.student_id) as active_students,
    SUM(el.duration_seconds) / 3600.0 as total_hours
FROM engagement_logs el
INNER JOIN students s ON el.student_id = s.student_id
WHERE {student_filter}
AND {date_filter}
GROUP BY DATE(el.timestamp)
ORDER BY date
"""

engagement_trend_df = db.execute_query_df(engagement_trend_query)

if not engagement_trend_df.empty and len(engagement_trend_df) > 0:
    engagement_trend_df['date'] = pd.to_datetime(engagement_trend_df['date'])
    
    fig = create_line_chart(
        engagement_trend_df,
        x='date',
        y='active_students',
        title="Daily Active Students",
        xlabel="Date",
        ylabel="Active Students"
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No engagement data available for the selected filters")

st.markdown("---")

# ============================================================================
# DATA TABLES
# ============================================================================

st.markdown("### 📋 Detailed Performance Data")

tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Student Performance Summary",
    "📚 Case Study Summary",
    "⚠️ At-Risk Students",
    "🎯 Rubric Details"
])

with tab1:
    st.markdown("#### Student Performance Summary")
    
    student_summary_query = f"""
    SELECT 
        s.student_id,
        s.name,
        s.cohort_id,
        s.department,
        s.campus,
        COUNT(DISTINCT a.case_id) as cases_attempted,
        AVG(a.score) as avg_score,
        MIN(a.score) as min_score,
        MAX(a.score) as max_score,
        AVG(a.ces_value) as avg_ces,
        SUM(a.duration_seconds) / 3600.0 as total_hours
    FROM students s
    LEFT JOIN attempts a ON s.student_id = a.student_id
    WHERE {student_filter}
    AND ({date_filter} OR a.attempt_id IS NULL)
    GROUP BY s.student_id, s.name, s.cohort_id, s.department, s.campus
    HAVING COUNT(a.attempt_id) > 0
    ORDER BY avg_score DESC
    """
    
    student_summary_df = db.execute_query_df(student_summary_query)
    
    if not student_summary_df.empty:
        # Format columns
        student_summary_df['avg_score'] = student_summary_df['avg_score'].apply(
            lambda x: f"{x:.1f}%" if pd.notna(x) else "N/A"
        )
        student_summary_df['min_score'] = student_summary_df['min_score'].apply(
            lambda x: f"{x:.0f}%" if pd.notna(x) else "N/A"
        )
        student_summary_df['max_score'] = student_summary_df['max_score'].apply(
            lambda x: f"{x:.0f}%" if pd.notna(x) else "N/A"
        )
        student_summary_df['avg_ces'] = student_summary_df['avg_ces'].apply(
            lambda x: f"{x:.1f}" if pd.notna(x) else "N/A"
        )
        student_summary_df['total_hours'] = student_summary_df['total_hours'].apply(
            lambda x: f"{x:.1f}h" if pd.notna(x) else "0h"
        )
        
        render_data_table(student_summary_df, f"student_performance_{datetime.now().strftime('%Y%m%d')}")
    else:
        st.info("No student performance data available")

with tab2:
    st.markdown("#### Case Study Performance Summary")
    
    case_summary_query = f"""
    SELECT 
        cs.title as case_study,
        COUNT(DISTINCT a.student_id) as students_attempted,
        AVG(a.score) as avg_score,
        MIN(a.score) as min_score,
        MAX(a.score) as max_score,
        AVG(a.ces_value) as avg_ces,
        AVG(a.duration_seconds) / 60.0 as avg_duration_min,
        COUNT(CASE WHEN a.attempt_number = 2 THEN 1 END) * 100.0 / 
            NULLIF(COUNT(CASE WHEN a.attempt_number = 1 THEN 1 END), 0) as retry_rate
    FROM case_studies cs
    LEFT JOIN attempts a ON cs.case_id = a.case_id
    INNER JOIN students s ON a.student_id = s.student_id
    WHERE {student_filter}
    AND {date_filter}
    GROUP BY cs.case_id, cs.title
    ORDER BY students_attempted DESC
    """
    
    case_summary_df = db.execute_query_df(case_summary_query)
    
    if not case_summary_df.empty:
        # Format columns
        case_summary_df['avg_score'] = case_summary_df['avg_score'].apply(
            lambda x: f"{x:.1f}%" if pd.notna(x) else "N/A"
        )
        case_summary_df['min_score'] = case_summary_df['min_score'].apply(
            lambda x: f"{x:.0f}%" if pd.notna(x) else "N/A"
        )
        case_summary_df['max_score'] = case_summary_df['max_score'].apply(
            lambda x: f"{x:.0f}%" if pd.notna(x) else "N/A"
        )
        case_summary_df['avg_ces'] = case_summary_df['avg_ces'].apply(
            lambda x: f"{x:.1f}" if pd.notna(x) else "N/A"
        )
        case_summary_df['avg_duration_min'] = case_summary_df['avg_duration_min'].apply(
            lambda x: f"{x:.1f} min" if pd.notna(x) else "N/A"
        )
        case_summary_df['retry_rate'] = case_summary_df['retry_rate'].apply(
            lambda x: f"{x:.1f}%" if pd.notna(x) else "0%"
        )
        
        render_data_table(case_summary_df, f"case_study_summary_{datetime.now().strftime('%Y%m%d')}")
    else:
        st.info("No case study data available")

with tab3:
    st.markdown("#### Students At Risk (Score < 60%)")
    
    at_risk_query = f"""
    SELECT 
        s.student_id,
        s.name,
        s.cohort_id,
        s.department,
        s.campus,
        COUNT(DISTINCT a.case_id) as cases_attempted,
        AVG(a.score) as avg_score,
        MIN(a.score) as lowest_score,
        COUNT(CASE WHEN a.score < 60 THEN 1 END) as failing_attempts,
        MAX(a.timestamp) as last_attempt_date
    FROM students s
    INNER JOIN attempts a ON s.student_id = a.student_id
    WHERE {student_filter}
    AND {date_filter}
    GROUP BY s.student_id, s.name, s.cohort_id, s.department, s.campus
    HAVING AVG(a.score) < 60 OR COUNT(CASE WHEN a.score < 60 THEN 1 END) > 0
    ORDER BY avg_score ASC
    """
    
    at_risk_df = db.execute_query_df(at_risk_query)
    
    if not at_risk_df.empty:
        # Format columns
        at_risk_df['avg_score'] = at_risk_df['avg_score'].apply(
            lambda x: f"{x:.1f}%" if pd.notna(x) else "N/A"
        )
        at_risk_df['lowest_score'] = at_risk_df['lowest_score'].apply(
            lambda x: f"{x:.0f}%" if pd.notna(x) else "N/A"
        )
        at_risk_df['last_attempt_date'] = pd.to_datetime(at_risk_df['last_attempt_date']).dt.strftime('%Y-%m-%d')
        
        st.warning(f"⚠️ {len(at_risk_df)} student(s) need attention")
        render_data_table(at_risk_df, f"at_risk_students_{datetime.now().strftime('%Y%m%d')}")
    else:
        st.success("✅ No at-risk students in the selected filters")

with tab4:
    st.markdown("#### Detailed Rubric Performance")
    
    rubric_detail_query = f"""
    SELECT 
        cs.title as case_study,
        rs.rubric_dimension,
        AVG(rs.score * 100.0 / NULLIF(rs.max_score, 0)) as avg_percentage,
        COUNT(DISTINCT a.student_id) as students_assessed,
        COUNT(CASE WHEN rs.improvement_flag = TRUE THEN 1 END) as needs_improvement_count,
        COUNT(CASE WHEN rs.improvement_flag = TRUE THEN 1 END) * 100.0 / 
            NULLIF(COUNT(*), 0) as improvement_rate
    FROM rubric_scores rs
    INNER JOIN attempts a ON rs.attempt_id = a.attempt_id
    INNER JOIN case_studies cs ON a.case_id = cs.case_id
    INNER JOIN students s ON a.student_id = s.student_id
    WHERE {student_filter}
    AND {date_filter}
    GROUP BY cs.title, rs.rubric_dimension
    ORDER BY cs.title, avg_percentage ASC
    """
    
    rubric_detail_df = db.execute_query_df(rubric_detail_query)
    
    if not rubric_detail_df.empty:
        # Format columns
        rubric_detail_df['avg_percentage'] = rubric_detail_df['avg_percentage'].apply(
            lambda x: f"{x:.1f}%" if pd.notna(x) else "N/A"
        )
        rubric_detail_df['improvement_rate'] = rubric_detail_df['improvement_rate'].apply(
            lambda x: f"{x:.1f}%" if pd.notna(x) else "0%"
        )
        
        render_data_table(rubric_detail_df, f"rubric_details_{datetime.now().strftime('%Y%m%d')}")
    else:
        st.info("No rubric data available")

st.markdown("---")
st.caption("💡 MIND Unified Dashboard | Miva Open University")
