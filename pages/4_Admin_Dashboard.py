"""
Admin Dashboard - Institution-Wide Analytics
Platform KPIs, trends, cross-cutting analytics, and executive reporting
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
    create_heatmap, create_box_plot, render_data_table, create_scatter_plot,
    create_pie_chart
)
from core.utils import (
    format_number, format_percentage, format_duration
)

# Page config
st.set_page_config(
    page_title="Admin Dashboard - MIND",
    page_icon="🔧",
    layout="wide"
)

# Apply theme
st.markdown(apply_streamlit_theme(), unsafe_allow_html=True)

# Require authentication
require_auth(allowed_roles=["Admin"])

# Get user info
user = get_current_user()

# Initialize database
db = get_db_manager()

# Header
st.markdown("# 🔧 Admin Dashboard")
st.markdown(f"### Welcome, {user['name']}!")
st.markdown("Institution-wide analytics, platform KPIs, and executive insights")
st.markdown("---")

# ============================================================================
# FILTERS SECTION
# ============================================================================

st.markdown("### 📊 Filters")

col1, col2, col3 = st.columns(3)

with col1:
    # Cohort filter
    cohorts_query = "SELECT DISTINCT cohort_id FROM students WHERE cohort_id IS NOT NULL ORDER BY cohort_id"
    cohorts_df = db.execute_query_df(cohorts_query)
    cohort_options = ['All'] + cohorts_df['cohort_id'].tolist() if not cohorts_df.empty else ['All']
    selected_cohort = st.selectbox("Cohort", cohort_options)

with col2:
    # Department filter
    dept_query = "SELECT DISTINCT department FROM students WHERE department IS NOT NULL ORDER BY department"
    dept_df = db.execute_query_df(dept_query)
    dept_options = ['All'] + dept_df['department'].tolist() if not dept_df.empty else ['All']
    selected_department = st.selectbox("Department", dept_options)

with col3:
    # Date range filter
    date_range = st.selectbox(
        "Time Period",
        ["Last 7 Days", "Last 30 Days", "Last 90 Days", "This Year", "All Time", "Custom Range"]
    )

# Convert date range selection to actual dates
if date_range == "Custom Range":
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", value=datetime.now() - timedelta(days=30))
    with col2:
        end_date = st.date_input("End Date", value=datetime.now())
    start_date = datetime.combine(start_date, datetime.min.time())
    end_date = datetime.combine(end_date, datetime.max.time())
else:
    date_range_map = {
        "Last 7 Days": 7,
        "Last 30 Days": 30,
        "Last 90 Days": 90,
        "This Year": 365,
        "All Time": 3650
    }
    days = date_range_map.get(date_range, 30)
    start_date = datetime.now() - timedelta(days=days)
    end_date = datetime.now()

st.markdown("---")

# ============================================================================
# BUILD DYNAMIC FILTERS
# ============================================================================

def build_student_filter():
    """Build WHERE clause for student filtering"""
    conditions = ["s.role = 'Student'"]
    
    if selected_cohort != 'All':
        conditions.append(f"s.cohort_id = '{selected_cohort}'")
    if selected_department != 'All':
        conditions.append(f"s.department = '{selected_department}'")
    
    return " AND ".join(conditions)

def build_date_filter(alias='a'):
    """Build date filter"""
    if start_date and end_date:
        return f"{alias}.timestamp >= '{start_date}' AND {alias}.timestamp <= '{end_date}'"
    return "1=1"

# ============================================================================
# EXECUTIVE SUMMARY KPIs
# ============================================================================

st.markdown("### 📈 Executive Summary")

student_filter = build_student_filter()
date_filter = build_date_filter()

kpi_query = f"""
WITH student_base AS (
    SELECT student_id, cohort_id, department, campus
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
        a.case_id,
        a.state
    FROM attempts a
    INNER JOIN student_base sb ON a.student_id = sb.student_id
    WHERE {date_filter}
),
student_stats AS (
    SELECT 
        COUNT(DISTINCT student_id) as total_students,
        COUNT(*) as total_attempts,
        AVG(score) as avg_score,
        AVG(ces_value) as avg_ces,
        SUM(duration_seconds) / 3600.0 as total_hours,
        COUNT(DISTINCT case_id) as cases_used,
        COUNT(CASE WHEN state = 'Completed' THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0) as completion_rate
    FROM student_attempts
),
improvement_stats AS (
    SELECT 
        AVG(CASE WHEN attempt_number = 2 THEN score END) - 
        AVG(CASE WHEN attempt_number = 1 THEN score END) as avg_improvement
    FROM student_attempts
    WHERE attempt_number IN (1, 2)
),
engagement_stats AS (
    SELECT 
        COUNT(DISTINCT el.student_id) as active_students_period,
        COUNT(DISTINCT el.session_id) as total_sessions
    FROM engagement_logs el
    INNER JOIN student_base sb ON el.student_id = sb.student_id
    WHERE {build_date_filter('el')}
)
SELECT 
    COALESCE(ss.total_students, 0) as total_students,
    COALESCE(ss.total_attempts, 0) as total_attempts,
    COALESCE(ss.avg_score, 0) as avg_score,
    COALESCE(ss.avg_ces, 0) as avg_ces,
    COALESCE(ss.total_hours, 0) as total_hours,
    COALESCE(ss.cases_used, 0) as cases_used,
    COALESCE(ss.completion_rate, 0) as completion_rate,
    COALESCE(i.avg_improvement, 0) as avg_improvement,
    COALESCE(es.active_students_period, 0) as active_students,
    COALESCE(es.total_sessions, 0) as total_sessions
FROM student_stats ss
CROSS JOIN improvement_stats i
CROSS JOIN engagement_stats es
"""

kpi_df = db.execute_query_df(kpi_query)

if not kpi_df.empty:
    kpi = kpi_df.iloc[0]
    
    total_students = int(kpi['total_students']) if pd.notna(kpi['total_students']) else 0
    total_attempts = int(kpi['total_attempts']) if pd.notna(kpi['total_attempts']) else 0
    avg_score = float(kpi['avg_score']) if pd.notna(kpi['avg_score']) else 0
    avg_ces = float(kpi['avg_ces']) if pd.notna(kpi['avg_ces']) else 0
    total_hours = float(kpi['total_hours']) if pd.notna(kpi['total_hours']) else 0
    cases_used = int(kpi['cases_used']) if pd.notna(kpi['cases_used']) else 0
    completion_rate = float(kpi['completion_rate']) if pd.notna(kpi['completion_rate']) else 0
    avg_improvement = float(kpi['avg_improvement']) if pd.notna(kpi['avg_improvement']) else 0
    active_students = int(kpi['active_students']) if pd.notna(kpi['active_students']) else 0
    total_sessions = int(kpi['total_sessions']) if pd.notna(kpi['total_sessions']) else 0
    
    # Calculate additional metrics
    avg_attempts_per_student = total_attempts / total_students if total_students > 0 else 0
    avg_hours_per_student = total_hours / total_students if total_students > 0 else 0
    
    metrics = [
        {
            'title': 'Total Students',
            'value': f"{total_students:,}",
            'accent': False
        },
        {
            'title': 'Active Students',
            'value': f"{active_students:,}",
            'accent': True
        },
        {
            'title': 'Total Attempts',
            'value': f"{total_attempts:,}",
            'accent': False
        },
        {
            'title': 'Platform Avg Score',
            'value': f"{avg_score:.1f}%",
            'accent': True
        },
        {
            'title': 'Completion Rate',
            'value': f"{completion_rate:.1f}%",
            'accent': True if completion_rate > 80 else False
        },
        {
            'title': 'Avg Improvement',
            'value': f"+{avg_improvement:.1f}%" if avg_improvement > 0 else f"{avg_improvement:.1f}%",
            'accent': True if avg_improvement > 0 else False
        },
        {
            'title': 'Total Learning Hours',
            'value': f"{total_hours:,.0f}h",
            'accent': False
        },
        {
            'title': 'Avg CES Score',
            'value': f"{avg_ces:.1f}",
            'accent': False
        },
        {
            'title': 'Case Studies Used',
            'value': cases_used,
            'accent': False
        },
        {
            'title': 'Total Sessions',
            'value': f"{total_sessions:,}",
            'accent': False
        },
        {
            'title': 'Avg Attempts/Student',
            'value': f"{avg_attempts_per_student:.1f}",
            'accent': False
        },
        {
            'title': 'Avg Hours/Student',
            'value': f"{avg_hours_per_student:.1f}h",
            'accent': False
        }
    ]
    
    render_metric_grid(metrics, columns=4)
else:
    st.info("📊 No data available for the selected filters")

st.markdown("---")

# ============================================================================
# INSTITUTIONAL TRENDS
# ============================================================================

st.markdown("### 📊 Institutional Trends")

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### 📈 Performance Trends Over Time")
    
    el_date_filter = build_date_filter('a')
    
    perf_trend_query = f"""
    SELECT 
        DATE(a.timestamp) as date,
        AVG(a.score) as avg_score,
        COUNT(DISTINCT a.student_id) as active_students,
        COUNT(*) as attempts
    FROM attempts a
    INNER JOIN students s ON a.student_id = s.student_id
    WHERE {student_filter}
    AND {el_date_filter}
    GROUP BY DATE(a.timestamp)
    ORDER BY date
    """
    
    perf_trend_df = db.execute_query_df(perf_trend_query)
    
    if not perf_trend_df.empty and len(perf_trend_df) > 0:
        perf_trend_df['date'] = pd.to_datetime(perf_trend_df['date'])
        
        fig = create_line_chart(
            perf_trend_df,
            x='date',
            y='avg_score',
            title="Daily Average Performance Score",
            x_label="Date",
            y_label="Average Score (%)"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No performance trend data available")

with col2:
    st.markdown("#### 👥 Student Engagement Trends")
    
    engagement_trend_query = f"""
    SELECT 
        DATE(a.timestamp) as date,
        COUNT(DISTINCT a.student_id) as active_students,
        COUNT(*) as total_attempts
    FROM attempts a
    INNER JOIN students s ON a.student_id = s.student_id
    WHERE {student_filter}
    AND {el_date_filter}
    GROUP BY DATE(a.timestamp)
    ORDER BY date
    """
    
    eng_trend_df = db.execute_query_df(engagement_trend_query)
    
    if not eng_trend_df.empty and len(eng_trend_df) > 0:
        eng_trend_df['date'] = pd.to_datetime(eng_trend_df['date'])
        
        fig = create_line_chart(
            eng_trend_df,
            x='date',
            y='active_students',
            title="Daily Active Students",
            x_label="Date",
            y_label="Active Students"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No engagement trend data available")

# Second row of trends
col3, col4 = st.columns(2)

with col3:
    st.markdown("#### ⏱️ Learning Hours Trend")
    
    hours_trend_query = f"""
    SELECT 
        DATE(a.timestamp) as date,
        SUM(a.duration_seconds) / 3600.0 as total_hours,
        AVG(a.duration_seconds) / 60.0 as avg_duration_min
    FROM attempts a
    INNER JOIN students s ON a.student_id = s.student_id
    WHERE {student_filter}
    AND {el_date_filter}
    GROUP BY DATE(a.timestamp)
    ORDER BY date
    """
    
    hours_trend_df = db.execute_query_df(hours_trend_query)
    
    if not hours_trend_df.empty and len(hours_trend_df) > 0:
        hours_trend_df['date'] = pd.to_datetime(hours_trend_df['date'])
        
        fig = create_line_chart(
            hours_trend_df,
            x='date',
            y='total_hours',
            title="Daily Total Learning Hours",
            x_label="Date",
            y_label="Total Hours"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No learning hours trend data available")

with col4:
    st.markdown("#### 📊 Completion Rate Trend")
    
    completion_trend_query = f"""
    SELECT 
        DATE(a.timestamp) as date,
        COUNT(CASE WHEN a.state = 'Completed' THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0) as completion_rate,
        COUNT(*) as total_attempts
    FROM attempts a
    INNER JOIN students s ON a.student_id = s.student_id
    WHERE {student_filter}
    AND {el_date_filter}
    GROUP BY DATE(a.timestamp)
    ORDER BY date
    """
    
    completion_trend_df = db.execute_query_df(completion_trend_query)
    
    if not completion_trend_df.empty and len(completion_trend_df) > 0:
        completion_trend_df['date'] = pd.to_datetime(completion_trend_df['date'])
        
        fig = create_line_chart(
            completion_trend_df,
            x='date',
            y='completion_rate',
            title="Daily Completion Rate",
            x_label="Date",
            y_label="Completion Rate (%)"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No completion rate trend data available")

st.markdown("---")

# ============================================================================
# CROSS-SECTIONAL ANALYSIS
# ============================================================================

st.markdown("### 🎯 Cross-Sectional Analysis")

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### 🏢 Performance by Department")
    
    dept_perf_query = f"""
    SELECT 
        s.department,
        COUNT(DISTINCT s.student_id) as student_count,
        AVG(a.score) as avg_score,
        COUNT(a.attempt_id) as total_attempts,
        AVG(a.ces_value) as avg_ces,
        SUM(a.duration_seconds) / 3600.0 as total_hours
    FROM students s
    LEFT JOIN attempts a ON s.student_id = a.student_id
    WHERE {student_filter}
    AND ({el_date_filter} OR a.attempt_id IS NULL)
    AND s.department IS NOT NULL
    GROUP BY s.department
    HAVING COUNT(a.attempt_id) > 0
    ORDER BY avg_score DESC
    """
    
    dept_perf_df = db.execute_query_df(dept_perf_query)
    
    if not dept_perf_df.empty and len(dept_perf_df) > 0:
        fig = create_bar_chart(
            dept_perf_df,
            x='department',
            y='avg_score',
            title="Average Score by Department",
            x_label="Department",
            y_label="Average Score (%)",
            color='avg_score'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No department performance data available")

with col2:
    st.markdown("#### 🏫 Performance by Campus")
    
    campus_perf_query = f"""
    SELECT 
        s.campus,
        COUNT(DISTINCT s.student_id) as student_count,
        AVG(a.score) as avg_score,
        COUNT(a.attempt_id) as total_attempts,
        SUM(a.duration_seconds) / 3600.0 as total_hours
    FROM students s
    LEFT JOIN attempts a ON s.student_id = a.student_id
    WHERE {student_filter}
    AND ({el_date_filter} OR a.attempt_id IS NULL)
    AND s.campus IS NOT NULL
    GROUP BY s.campus
    HAVING COUNT(a.attempt_id) > 0
    ORDER BY avg_score DESC
    """
    
    campus_perf_df = db.execute_query_df(campus_perf_query)
    
    if not campus_perf_df.empty and len(campus_perf_df) > 0:
        fig = create_bar_chart(
            campus_perf_df,
            x='campus',
            y='avg_score',
            title="Average Score by Campus",
            x_label="Campus",
            y_label="Average Score (%)",
            color='avg_score'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No campus performance data available")

# Third row
col5, col6 = st.columns(2)

with col5:
    st.markdown("#### 👥 Student Distribution by Cohort")
    
    cohort_dist_query = f"""
    SELECT 
        cohort_id,
        COUNT(*) as student_count
    FROM students s
    WHERE {student_filter}
    AND cohort_id IS NOT NULL
    GROUP BY cohort_id
    ORDER BY student_count DESC
    LIMIT 10
    """
    
    cohort_dist_df = db.execute_query_df(cohort_dist_query)
    
    if not cohort_dist_df.empty and len(cohort_dist_df) > 0:
        fig = create_pie_chart(
            cohort_dist_df,
            names='cohort_id',
            values='student_count',
            title="Student Distribution by Cohort (Top 10)"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No cohort distribution data available")

with col6:
    st.markdown("#### 📚 Case Study Usage")
    
    case_usage_query = f"""
    SELECT 
        cs.title as case_study,
        COUNT(DISTINCT a.student_id) as unique_students,
        COUNT(a.attempt_id) as total_attempts,
        AVG(a.score) as avg_score
    FROM case_studies cs
    LEFT JOIN attempts a ON cs.case_id = a.case_id
    INNER JOIN students s ON a.student_id = s.student_id
    WHERE {student_filter}
    AND {el_date_filter}
    GROUP BY cs.case_id, cs.title
    HAVING COUNT(a.attempt_id) > 0
    ORDER BY total_attempts DESC
    """
    
    case_usage_df = db.execute_query_df(case_usage_query)
    
    if not case_usage_df.empty and len(case_usage_df) > 0:
        fig = create_bar_chart(
            case_usage_df,
            x='case_study',
            y='total_attempts',
            title="Attempts by Case Study",
            x_label="Case Study",
            y_label="Total Attempts",
            color='total_attempts'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No case study usage data available")

st.markdown("---")

# ============================================================================
# SYSTEM & ENVIRONMENT OVERVIEW
# ============================================================================

st.markdown("### 🖥️ System & Environment Overview")

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### ⚡ System Performance Summary")
    
    system_summary_query = """
    SELECT 
        AVG(latency_ms) as avg_latency,
        MAX(latency_ms) as max_latency,
        AVG(error_rate) as avg_error_rate,
        AVG(reliability_index) as avg_reliability,
        COUNT(CASE WHEN severity = 'Critical' THEN 1 END) as critical_incidents
    FROM system_reliability
    WHERE timestamp >= NOW() - INTERVAL '30 days'
    """
    
    system_summary_df = db.execute_query_df(system_summary_query)
    
    if not system_summary_df.empty:
        sys = system_summary_df.iloc[0]
        
        st.markdown(f"""
        <div style="
            background-color: {COLORS['white']};
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        ">
            <h4 style="color: {COLORS['primary']}; margin-top: 0;">Last 30 Days</h4>
            <p><strong>Avg Latency:</strong> {sys['avg_latency']:.0f} ms</p>
            <p><strong>Max Latency:</strong> {sys['max_latency']:.0f} ms</p>
            <p><strong>Avg Error Rate:</strong> {sys['avg_error_rate']:.2f}%</p>
            <p><strong>Avg Reliability:</strong> {sys['avg_reliability']:.1f}%</p>
            <p><strong>Critical Incidents:</strong> {int(sys['critical_incidents'])}</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("No system performance data available")

with col2:
    st.markdown("#### 🌍 Environment Quality Summary")
    
    env_summary_query = """
    SELECT 
        AVG(noise_level) as avg_noise,
        AVG(internet_stability_score) as avg_stability,
        AVG(internet_latency_ms) as avg_latency,
        AVG(connection_drops) as avg_drops,
        COUNT(*) as total_attempts
    FROM environment_metrics
    """
    
    env_summary_df = db.execute_query_df(env_summary_query)
    
    if not env_summary_df.empty:
        env = env_summary_df.iloc[0]
        
        st.markdown(f"""
        <div style="
            background-color: {COLORS['white']};
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        ">
            <h4 style="color: {COLORS['primary']}; margin-top: 0;">All Time</h4>
            <p><strong>Avg Noise Level:</strong> {env['avg_noise']:.0f} dB</p>
            <p><strong>Avg Internet Stability:</strong> {env['avg_stability']:.1f}%</p>
            <p><strong>Avg Internet Latency:</strong> {env['avg_latency']:.0f} ms</p>
            <p><strong>Avg Connection Drops:</strong> {env['avg_drops']:.1f}</p>
            <p><strong>Total Attempts Monitored:</strong> {int(env['total_attempts']):,}</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("No environment quality data available")

st.markdown("---")

# ============================================================================
# ADMINISTRATIVE DATA TABLES
# ============================================================================

st.markdown("### 📋 Administrative Reports")

tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Department Summary",
    "🏫 Campus Summary",
    "📚 Case Study Analytics",
    "🎯 Performance Benchmarks"
])

with tab1:
    st.markdown("#### Department Performance Summary")
    
    dept_summary_query = f"""
    SELECT 
        s.department,
        COUNT(DISTINCT s.student_id) as total_students,
        COUNT(DISTINCT CASE WHEN a.attempt_id IS NOT NULL THEN s.student_id END) as active_students,
        COUNT(a.attempt_id) as total_attempts,
        AVG(a.score) as avg_score,
        MIN(a.score) as min_score,
        MAX(a.score) as max_score,
        AVG(a.ces_value) as avg_ces,
        SUM(a.duration_seconds) / 3600.0 as total_hours,
        COUNT(CASE WHEN a.score < 60 THEN 1 END) as at_risk_attempts
    FROM students s
    LEFT JOIN attempts a ON s.student_id = a.student_id
    WHERE {student_filter}
    AND ({el_date_filter} OR a.attempt_id IS NULL)
    AND s.department IS NOT NULL
    GROUP BY s.department
    ORDER BY avg_score DESC
    """
    
    dept_summary_df = db.execute_query_df(dept_summary_query)
    
    if not dept_summary_df.empty:
        dept_summary_df['active_rate'] = (dept_summary_df['active_students'] / dept_summary_df['total_students'] * 100).fillna(0)
        dept_summary_df['avg_score'] = dept_summary_df['avg_score'].apply(
            lambda x: f"{x:.1f}%" if pd.notna(x) else "N/A"
        )
        dept_summary_df['min_score'] = dept_summary_df['min_score'].apply(
            lambda x: f"{x:.0f}%" if pd.notna(x) else "N/A"
        )
        dept_summary_df['max_score'] = dept_summary_df['max_score'].apply(
            lambda x: f"{x:.0f}%" if pd.notna(x) else "N/A"
        )
        dept_summary_df['avg_ces'] = dept_summary_df['avg_ces'].apply(
            lambda x: f"{x:.1f}" if pd.notna(x) else "N/A"
        )
        dept_summary_df['total_hours'] = dept_summary_df['total_hours'].apply(
            lambda x: f"{x:.0f}h" if pd.notna(x) else "0h"
        )
        dept_summary_df['active_rate'] = dept_summary_df['active_rate'].apply(
            lambda x: f"{x:.1f}%" if pd.notna(x) else "N/A"
        )
        
        render_data_table(dept_summary_df, f"department_summary_{datetime.now().strftime('%Y%m%d')}")
    else:
        st.info("No department summary data available")

with tab2:
    st.markdown("#### Campus Performance Summary")
    
    campus_summary_query = f"""
    SELECT 
        s.campus,
        COUNT(DISTINCT s.student_id) as total_students,
        COUNT(DISTINCT CASE WHEN a.attempt_id IS NOT NULL THEN s.student_id END) as active_students,
        COUNT(a.attempt_id) as total_attempts,
        AVG(a.score) as avg_score,
        AVG(a.ces_value) as avg_ces,
        SUM(a.duration_seconds) / 3600.0 as total_hours,
        COUNT(DISTINCT a.case_id) as cases_used
    FROM students s
    LEFT JOIN attempts a ON s.student_id = a.student_id
    WHERE {student_filter}
    AND ({el_date_filter} OR a.attempt_id IS NULL)
    AND s.campus IS NOT NULL
    GROUP BY s.campus
    ORDER BY avg_score DESC
    """
    
    campus_summary_df = db.execute_query_df(campus_summary_query)
    
    if not campus_summary_df.empty:
        campus_summary_df['active_rate'] = (campus_summary_df['active_students'] / campus_summary_df['total_students'] * 100).fillna(0)
        campus_summary_df['avg_score'] = campus_summary_df['avg_score'].apply(
            lambda x: f"{x:.1f}%" if pd.notna(x) else "N/A"
        )
        campus_summary_df['avg_ces'] = campus_summary_df['avg_ces'].apply(
            lambda x: f"{x:.1f}" if pd.notna(x) else "N/A"
        )
        campus_summary_df['total_hours'] = campus_summary_df['total_hours'].apply(
            lambda x: f"{x:.0f}h" if pd.notna(x) else "0h"
        )
        campus_summary_df['active_rate'] = campus_summary_df['active_rate'].apply(
            lambda x: f"{x:.1f}%" if pd.notna(x) else "N/A"
        )
        
        render_data_table(campus_summary_df, f"campus_summary_{datetime.now().strftime('%Y%m%d')}")
    else:
        st.info("No campus summary data available")

with tab3:
    st.markdown("#### Case Study Analytics")
    
    case_analytics_query = f"""
    SELECT 
        cs.title as case_study,
        COUNT(DISTINCT a.student_id) as unique_students,
        COUNT(a.attempt_id) as total_attempts,
        AVG(a.score) as avg_score,
        MIN(a.score) as min_score,
        MAX(a.score) as max_score,
        AVG(a.duration_seconds) / 60.0 as avg_duration_min,
        COUNT(CASE WHEN a.attempt_number = 2 THEN 1 END) * 100.0 / 
            NULLIF(COUNT(CASE WHEN a.attempt_number = 1 THEN 1 END), 0) as retry_rate,
        AVG(a.ces_value) as avg_ces
    FROM case_studies cs
    LEFT JOIN attempts a ON cs.case_id = a.case_id
    INNER JOIN students s ON a.student_id = s.student_id
    WHERE {student_filter}
    AND {el_date_filter}
    GROUP BY cs.case_id, cs.title
    HAVING COUNT(a.attempt_id) > 0
    ORDER BY total_attempts DESC
    """
    
    case_analytics_df = db.execute_query_df(case_analytics_query)
    
    if not case_analytics_df.empty:
        case_analytics_df['avg_score'] = case_analytics_df['avg_score'].apply(
            lambda x: f"{x:.1f}%" if pd.notna(x) else "N/A"
        )
        case_analytics_df['min_score'] = case_analytics_df['min_score'].apply(
            lambda x: f"{x:.0f}%" if pd.notna(x) else "N/A"
        )
        case_analytics_df['max_score'] = case_analytics_df['max_score'].apply(
            lambda x: f"{x:.0f}%" if pd.notna(x) else "N/A"
        )
        case_analytics_df['avg_duration_min'] = case_analytics_df['avg_duration_min'].apply(
            lambda x: f"{x:.1f} min" if pd.notna(x) else "N/A"
        )
        case_analytics_df['retry_rate'] = case_analytics_df['retry_rate'].apply(
            lambda x: f"{x:.1f}%" if pd.notna(x) else "0%"
        )
        case_analytics_df['avg_ces'] = case_analytics_df['avg_ces'].apply(
            lambda x: f"{x:.1f}" if pd.notna(x) else "N/A"
        )
        
        render_data_table(case_analytics_df, f"case_analytics_{datetime.now().strftime('%Y%m%d')}")
    else:
        st.info("No case study analytics available")

with tab4:
    st.markdown("#### Performance Benchmarks")
    
    benchmarks_query = f"""
    SELECT 
        'Platform Average' as metric,
        AVG(score) as value,
        'Overall student performance' as description
    FROM attempts a
    INNER JOIN students s ON a.student_id = s.student_id
    WHERE {student_filter}
    AND {el_date_filter}
    
    UNION ALL
    
    SELECT 
        'Completion Rate' as metric,
        COUNT(CASE WHEN state = 'Completed' THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0) as value,
        'Percentage of completed attempts' as description
    FROM attempts a
    INNER JOIN students s ON a.student_id = s.student_id
    WHERE {student_filter}
    AND {el_date_filter}
    
    UNION ALL
    
    SELECT 
        'Average CES' as metric,
        AVG(ces_value) as value,
        'Customer Effort Score' as description
    FROM attempts a
    INNER JOIN students s ON a.student_id = s.student_id
    WHERE {student_filter}
    AND {el_date_filter}
    
    UNION ALL
    
    SELECT 
        'Avg Learning Hours/Student' as metric,
        SUM(duration_seconds) / 3600.0 / NULLIF(COUNT(DISTINCT a.student_id), 0) as value,
        'Total hours per student' as description
    FROM attempts a
    INNER JOIN students s ON a.student_id = s.student_id
    WHERE {student_filter}
    AND {el_date_filter}
    
    UNION ALL
    
    SELECT 
        'Student Engagement Rate' as metric,
        COUNT(DISTINCT a.student_id) * 100.0 / 
            NULLIF((SELECT COUNT(*) FROM students s2 WHERE {student_filter.replace('s.', 's2.')}), 0) as value,
        'Percentage of students with attempts' as description
    FROM attempts a
    INNER JOIN students s ON a.student_id = s.student_id
    WHERE {student_filter}
    AND {el_date_filter}
    """
    
    benchmarks_df = db.execute_query_df(benchmarks_query)
    
    if not benchmarks_df.empty:
        benchmarks_df['value'] = benchmarks_df['value'].apply(
            lambda x: f"{x:.2f}" if pd.notna(x) else "N/A"
        )
        
        render_data_table(benchmarks_df, f"performance_benchmarks_{datetime.now().strftime('%Y%m%d')}")
    else:
        st.info("No benchmark data available")

st.markdown("---")
st.caption("💡 MIND Unified Dashboard | Miva Open University")
