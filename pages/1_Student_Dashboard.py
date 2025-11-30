"""
Student Dashboard - Personal Performance Analytics
View scores, rubric feedback, engagement, and progress
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta

from auth import require_auth, get_student_id, get_current_user
from theme import apply_streamlit_theme, COLORS
from db import init_database
from core.components import (
    render_kpi_card, render_metric_grid, create_line_chart, create_bar_chart,
    create_scatter_plot, create_histogram, render_data_table, create_gauge_chart
)
from core.utils import (
    format_number, format_percentage, format_duration, get_date_range_filter,
    calculate_rubric_mastery
)
from core.queries.attempts_queries import (
    get_student_attempts, get_student_performance_summary,
    get_attempt_improvement, get_score_trend
)
from core.queries.rubric_queries import (
    get_student_rubric_scores, get_rubric_mastery_by_dimension
)
from core.queries.engagement_queries import (
    get_student_engagement, get_student_active_days,
    get_engagement_summary_by_student, get_daily_engagement_trend,
    get_engagement_by_action_type
)

# Page config
st.set_page_config(
    page_title="Student Dashboard - MIND",
    page_icon="👨‍🎓",
    layout="wide"
)

# Apply theme
st.markdown(apply_streamlit_theme(), unsafe_allow_html=True)

# Require authentication
require_auth(allowed_roles=["Student", "Admin"])

# Get user info
user = get_current_user()
student_id = user.get('student_id') or 'STU001'  # Fallback for admin viewing

# Initialize database
db = init_database()

# Header
st.markdown("# 👨‍🎓 Student Dashboard")
st.markdown(f"### Welcome back, {user['name']}!")
st.markdown("---")

# Date filter in sidebar
with st.sidebar:
    st.markdown("### 📅 Filters")
    
    date_range_option = st.selectbox(
        "Time Period",
        ["Last 7 Days", "Last 30 Days", "Last 90 Days", "All Time", "Custom Range"]
    )
    
    if date_range_option == "Custom Range":
        start_date, end_date = get_date_range_filter(default_days=30)
    else:
        days_map = {
            "Last 7 Days": 7,
            "Last 30 Days": 30,
            "Last 90 Days": 90,
            "All Time": 3650
        }
        days = days_map[date_range_option]
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
    
    st.markdown("---")
    st.markdown("### 📊 View Options")
    show_details = st.checkbox("Show Detailed Tables", value=True)

# ============================================
# KEY PERFORMANCE INDICATORS
# ============================================

st.markdown("## 📊 Key Performance Indicators")

# Fetch performance summary
summary_query = get_student_performance_summary(student_id)
summary_df = db.execute_query_df(summary_query)

if not summary_df.empty:
    summary = summary_df.iloc[0]
    
    # Safely get values with defaults for None/NaN
    total_cases = summary['total_cases_attempted'] if pd.notna(summary['total_cases_attempted']) else 0
    avg_score = summary['avg_score'] if pd.notna(summary['avg_score']) else 0
    avg_ces = summary['avg_ces'] if pd.notna(summary['avg_ces']) else 0
    avg_duration = summary['avg_duration'] if pd.notna(summary['avg_duration']) else 0
    max_score = summary['max_score'] if pd.notna(summary['max_score']) else 0
    
    # Calculate additional metrics
    active_days_query = get_student_active_days(student_id)
    active_days_df = db.execute_query_df(active_days_query)
    active_days = active_days_df.iloc[0]['active_days'] if not active_days_df.empty else 0
    active_days = active_days if pd.notna(active_days) else 0
    
    # Engagement summary
    engagement_query = get_engagement_summary_by_student(student_id)
    engagement_df = db.execute_query_df(engagement_query)
    
    total_duration = 0
    if not engagement_df.empty:
        total_duration = engagement_df.iloc[0]['total_duration_seconds']
        total_duration = total_duration if pd.notna(total_duration) else 0
    
    # Rubric mastery
    rubric_query = get_rubric_mastery_by_dimension(student_id)
    rubric_df = db.execute_query_df(rubric_query)
    avg_rubric_mastery = rubric_df['avg_percentage'].mean() if not rubric_df.empty else 0
    avg_rubric_mastery = avg_rubric_mastery if pd.notna(avg_rubric_mastery) else 0
    
    # Display KPI cards
    metrics = [
        {
            'title': 'Cases Attempted',
            'value': int(total_cases),
            'accent': False
        },
        {
            'title': 'Average Score',
            'value': f"{avg_score:.1f}%" if avg_score > 0 else "N/A",
            'accent': True
        },
        {
            'title': 'Average CES',
            'value': f"{avg_ces:.1f}" if avg_ces > 0 else "N/A",
            'accent': False
        },
        {
            'title': 'Avg Time on Task',
            'value': format_duration(int(avg_duration)),
            'accent': False
        },
        {
            'title': 'Active Days',
            'value': int(active_days),
            'accent': False
        },
        {
            'title': 'Total Engagement Time',
            'value': format_duration(int(total_duration)),
            'accent': False
        },
        {
            'title': 'Rubric Mastery',
            'value': f"{avg_rubric_mastery:.1f}%" if avg_rubric_mastery > 0 else "N/A",
            'accent': True
        },
        {
            'title': 'Best Score',
            'value': f"{max_score:.0f}%" if max_score > 0 else "N/A",
            'accent': False
        }
    ]
    
    render_metric_grid(metrics, columns=4)

else:
    st.info("📊 **No performance data available yet**")
    st.markdown("""
    ### Getting Started
    
    To see your performance metrics:
    1. Complete case studies in the MIND platform
    2. Your attempts will be recorded in the database
    3. Return to this dashboard to view your analytics
    
    ### What You'll See
    Once you have data, this dashboard will show:
    - 📈 Your scores and improvement trends
    - 📊 Rubric feedback and mastery levels
    - 🎯 Engagement activity and time on task
    - 📋 Detailed history of all your attempts
    
    **Student ID**: `{student_id}`  
    **Database**: Connected ✅
    """)
    
    # Show sample KPI cards with zero values
    st.markdown("---")
    st.markdown("### Preview: What Your Dashboard Will Look Like")
    
    metrics = [
        {'title': 'Cases Attempted', 'value': 0, 'accent': False},
        {'title': 'Average Score', 'value': 'N/A', 'accent': True},
        {'title': 'Average CES', 'value': 'N/A', 'accent': False},
        {'title': 'Avg Time on Task', 'value': '0m 0s', 'accent': False},
        {'title': 'Active Days', 'value': 0, 'accent': False},
        {'title': 'Total Engagement Time', 'value': '0m 0s', 'accent': False},
        {'title': 'Rubric Mastery', 'value': 'N/A', 'accent': True},
        {'title': 'Best Score', 'value': 'N/A', 'accent': False}
    ]
    
    render_metric_grid(metrics, columns=4)

st.markdown("---")

# ============================================
# CHARTS SECTION
# ============================================

st.markdown("## 📈 Performance Analytics")

col1, col2 = st.columns(2)

with col1:
    # Score trend over time
    score_trend_query = get_score_trend(student_id)
    score_trend_df = db.execute_query_df(score_trend_query)
    
    if not score_trend_df.empty:
        fig = create_line_chart(
            score_trend_df,
            x='timestamp',
            y='score',
            title='Score Trend Over Time',
            x_label='Date',
            y_label='Score (%)'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Complete case studies to see your score trend")

with col2:
    # Attempt improvement
    improvement_query = get_attempt_improvement(student_id)
    improvement_df = db.execute_query_df(improvement_query)
    
    if not improvement_df.empty and 'improvement' in improvement_df.columns:
        # Filter out null improvements
        improvement_df = improvement_df[improvement_df['improvement'].notna()]
        
        if not improvement_df.empty:
            fig = create_bar_chart(
                improvement_df,
                x='case_title',
                y='improvement',
                title='Improvement: Attempt 1 vs 2',
                y_label='Score Improvement (points)'
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Complete second attempts to see improvements")
    else:
        st.info("Complete second attempts to see improvements")

# Second row of charts
col3, col4 = st.columns(2)

with col3:
    # Rubric dimension mastery
    
    if not rubric_df.empty:
        fig = create_bar_chart(
            rubric_df,
            x='avg_percentage',
            y='rubric_dimension',
            title='Rubric Dimension Mastery',
            orientation='h',
            x_label='Mastery (%)',
            y_label='Dimension'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Complete assessments to see rubric mastery")

with col4:
    # Engagement by action type
    action_query = get_engagement_by_action_type(student_id)
    action_df = db.execute_query_df(action_query)
    
    if not action_df.empty:
        from core.components import create_pie_chart
        fig = create_pie_chart(
            action_df,
            names='action_type',
            values='action_count',
            title='Engagement by Action Type'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Engagement data will appear here")

# Daily engagement trend
daily_engagement_query = get_daily_engagement_trend(student_id, days=30)
daily_engagement_df = db.execute_query_df(daily_engagement_query)

if not daily_engagement_df.empty:
    fig = create_line_chart(
        daily_engagement_df,
        x='date',
        y='total_duration',
        title='Daily Engagement Activity',
        x_label='Date',
        y_label='Total Duration (seconds)'
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Daily engagement data will appear here")

st.markdown("---")

# ============================================
# DETAILED TABLES
# ============================================

if show_details:
    st.markdown("## 📋 Detailed Data")
    
    tab1, tab2, tab3 = st.tabs(["📝 Attempt History", "📊 Rubric Scores", "🎯 Engagement Logs"])
    
    with tab1:
        st.markdown("### Attempt History")
        attempts_query = get_student_attempts(
            student_id,
            start_date.isoformat() if date_range_option != "All Time" else None,
            end_date.isoformat()
        )
        attempts_df = db.execute_query_df(attempts_query)
        
        if not attempts_df.empty:
            # Format the dataframe
            display_df = attempts_df[['case_title', 'attempt_number', 'score', 
                                     'duration_seconds', 'ces_value', 'timestamp', 'state']].copy()
            display_df['duration'] = display_df['duration_seconds'].apply(format_duration)
            display_df = display_df.drop('duration_seconds', axis=1)
            display_df.columns = ['Case', 'Attempt #', 'Score', 'CES', 'Date', 'Status', 'Duration']
            
            render_data_table(display_df, height=400)
            
            # Download button
            csv = attempts_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Attempts Data",
                data=csv,
                file_name=f"my_attempts_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.info("No attempts found in the selected date range")
    
    with tab2:
        st.markdown("### Rubric Scores & Feedback")
        rubric_scores_query = get_student_rubric_scores(student_id)
        rubric_scores_df = db.execute_query_df(rubric_scores_query)
        
        if not rubric_scores_df.empty:
            # Format the dataframe
            display_df = rubric_scores_df[['case_title', 'attempt_number', 'rubric_dimension', 
                                          'score', 'max_score', 'percentage', 
                                          'improvement_flag', 'comment']].copy()
            display_df.columns = ['Case', 'Attempt #', 'Dimension', 'Score', 
                                 'Max Score', 'Percentage', 'Needs Improvement', 'Feedback']
            
            render_data_table(display_df, height=400)
            
            # Download button
            csv = rubric_scores_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Rubric Scores",
                data=csv,
                file_name=f"my_rubric_scores_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.info("No rubric scores available")
    
    with tab3:
        st.markdown("### Engagement Session Logs")
        engagement_query = get_student_engagement(
            student_id,
            start_date.isoformat() if date_range_option != "All Time" else None,
            end_date.isoformat()
        )
        engagement_data_df = db.execute_query_df(engagement_query)
        
        if not engagement_data_df.empty:
            # Format the dataframe
            display_df = engagement_data_df[['case_title', 'session_id', 'action_type', 
                                            'session_phase', 'duration_seconds', 'timestamp']].copy()
            display_df['duration'] = display_df['duration_seconds'].apply(format_duration)
            display_df = display_df.drop('duration_seconds', axis=1)
            display_df.columns = ['Case', 'Session ID', 'Action', 'Phase', 'Timestamp', 'Duration']
            
            render_data_table(display_df, height=400)
            
            # Download button
            csv = engagement_data_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Engagement Logs",
                data=csv,
                file_name=f"my_engagement_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.info("No engagement logs in the selected date range")

# Footer
st.markdown("---")
st.caption("💡 MIND Unified Dashboard | Miva Open University")
