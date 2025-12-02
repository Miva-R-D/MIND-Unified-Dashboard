"""
Developer Dashboard - System Health & Environment Monitoring
Monitor API performance, system reliability, and environment quality metrics
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from auth import require_auth, get_current_user
from theme_toggle import apply_theme, create_theme_toggle
from theme import apply_streamlit_theme, COLORS
from db import get_db_manager
from core.components import (
    render_kpi_card, render_metric_grid, create_line_chart, create_bar_chart,
    create_heatmap, create_box_plot, render_data_table, create_scatter_plot
)
from core.utils import (
    format_number, format_percentage, format_duration
)

# Apply theme CSS (must be first)
apply_theme()

# Page config
st.set_page_config(
    page_title="Developer Dashboard - MIND",
    page_icon="👨‍💻",
    layout="wide"
)

# Apply custom theme
st.markdown(apply_streamlit_theme(), unsafe_allow_html=True)

# Require authentication
require_auth(allowed_roles=["Developer", "Admin"])

# Get user info
user = get_current_user()

# Initialize database
db = get_db_manager()

# Header
st.markdown("# 👨‍💻 Developer Dashboard")
st.markdown(f"### Welcome, {user['name']}!")
st.markdown("Monitor system health, API performance, and environment quality metrics")
st.markdown("---")

# ============================================================================
# FILTERS SECTION
# ============================================================================

# Theme toggle in sidebar
with st.sidebar:
    create_theme_toggle()

st.markdown("---")
st.markdown("### 🔧 Filters")

col1, col2, col3, col4 = st.columns(4)

with col1:
    # API filter
    api_query = "SELECT DISTINCT api_name FROM system_reliability WHERE api_name IS NOT NULL ORDER BY api_name"
    api_df = db.execute_query_df(api_query)
    api_options = ['All'] + api_df['api_name'].tolist() if not api_df.empty else ['All']
    selected_api = st.selectbox("API Service", api_options)

with col2:
    # Location filter
    location_query = "SELECT DISTINCT location FROM system_reliability WHERE location IS NOT NULL ORDER BY location"
    location_df = db.execute_query_df(location_query)
    location_options = ['All'] + location_df['location'].tolist() if not location_df.empty else ['All']
    selected_location = st.selectbox("Location", location_options)

with col3:
    # Severity filter
    severity_options = ['All', 'Info', 'Warning', 'Critical']
    selected_severity = st.selectbox("Severity", severity_options)

with col4:
    # Date range filter
    date_range = st.selectbox(
        "Time Period",
        ["Last 24 Hours", "Last 7 Days", "Last 30 Days", "All Time", "Custom Range"]
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
        "Last 24 Hours": 1,
        "Last 7 Days": 7,
        "Last 30 Days": 30,
        "All Time": 3650
    }
    days = date_range_map.get(date_range, 30)
    start_date = datetime.now() - timedelta(days=days)
    end_date = datetime.now()

st.markdown("---")

# ============================================================================
# BUILD DYNAMIC FILTERS
# ============================================================================

def build_system_filter(alias='sr'):
    """Build WHERE clause for system reliability filtering"""
    conditions = ["1=1"]
    
    if selected_api != 'All':
        conditions.append(f"{alias}.api_name = '{selected_api}'")
    if selected_location != 'All':
        conditions.append(f"{alias}.location = '{selected_location}'")
    if selected_severity != 'All':
        conditions.append(f"{alias}.severity = '{selected_severity}'")
    
    return " AND ".join(conditions)

def build_date_filter(alias='sr'):
    """Build date filter"""
    if start_date and end_date:
        return f"{alias}.timestamp >= '{start_date}' AND {alias}.timestamp <= '{end_date}'"
    return "1=1"

# ============================================================================
# SYSTEM HEALTH KPIs
# ============================================================================

st.markdown("### 📊 System Health Overview")

system_filter = build_system_filter()
date_filter = build_date_filter()

kpi_query = f"""
WITH system_stats AS (
    SELECT 
        AVG(latency_ms) as avg_latency,
        MAX(latency_ms) as max_latency,
        AVG(error_rate) as avg_error_rate,
        AVG(reliability_index) as avg_reliability,
        COUNT(*) as total_records,
        COUNT(DISTINCT api_name) as api_count
    FROM system_reliability sr
    WHERE {system_filter}
    AND {date_filter}
),
severity_counts AS (
    SELECT 
        COUNT(CASE WHEN severity = 'Critical' THEN 1 END) as critical_count,
        COUNT(CASE WHEN severity = 'Warning' THEN 1 END) as warning_count,
        COUNT(CASE WHEN severity = 'Info' THEN 1 END) as info_count
    FROM system_reliability sr
    WHERE {system_filter}
    AND {date_filter}
)
SELECT 
    COALESCE(ss.avg_latency, 0) as avg_latency,
    COALESCE(ss.max_latency, 0) as max_latency,
    COALESCE(ss.avg_error_rate, 0) as avg_error_rate,
    COALESCE(ss.avg_reliability, 0) as avg_reliability,
    COALESCE(ss.total_records, 0) as total_records,
    COALESCE(ss.api_count, 0) as api_count,
    COALESCE(sc.critical_count, 0) as critical_count,
    COALESCE(sc.warning_count, 0) as warning_count
FROM system_stats ss
CROSS JOIN severity_counts sc
"""

kpi_df = db.execute_query_df(kpi_query)

if not kpi_df.empty:
    kpi = kpi_df.iloc[0]
    
    avg_latency = float(kpi['avg_latency']) if pd.notna(kpi['avg_latency']) else 0
    max_latency = float(kpi['max_latency']) if pd.notna(kpi['max_latency']) else 0
    avg_error_rate = float(kpi['avg_error_rate']) if pd.notna(kpi['avg_error_rate']) else 0
    avg_reliability = float(kpi['avg_reliability']) if pd.notna(kpi['avg_reliability']) else 0
    api_count = int(kpi['api_count']) if pd.notna(kpi['api_count']) else 0
    critical_count = int(kpi['critical_count']) if pd.notna(kpi['critical_count']) else 0
    warning_count = int(kpi['warning_count']) if pd.notna(kpi['warning_count']) else 0
    
    metrics = [
        {
            'title': 'Avg API Latency',
            'value': f"{avg_latency:.0f} ms",
            'accent': True if avg_latency > 200 else False
        },
        {
            'title': 'Max Latency',
            'value': f"{max_latency:.0f} ms",
            'accent': True if max_latency > 500 else False
        },
        {
            'title': 'Avg Error Rate',
            'value': f"{avg_error_rate:.2f}%",
            'accent': True if avg_error_rate > 1.0 else False
        },
        {
            'title': 'Avg Reliability',
            'value': f"{avg_reliability:.1f}%",
            'accent': True if avg_reliability < 95 else False
        },
        {
            'title': 'API Services',
            'value': api_count,
            'accent': False
        },
        {
            'title': 'Critical Alerts',
            'value': critical_count,
            'accent': True if critical_count > 0 else False
        },
        {
            'title': 'Warnings',
            'value': warning_count,
            'accent': True if warning_count > 10 else False
        },
        {
            'title': 'System Uptime',
            'value': f"{avg_reliability:.1f}%",
            'accent': False
        }
    ]
    
    render_metric_grid(metrics, columns=4)
else:
    st.info("📊 No system data available for the selected filters")

st.markdown("---")

# ============================================================================
# API PERFORMANCE CHARTS
# ============================================================================

st.markdown("### 📈 API Performance Analytics")

col1, col2 = st.columns(2)

with col1:
    
    latency_query = f"""
    SELECT 
        api_name,
        AVG(latency_ms) as avg_latency,
        MIN(latency_ms) as min_latency,
        MAX(latency_ms) as max_latency,
        COUNT(*) as request_count
    FROM system_reliability sr
    WHERE {system_filter}
    AND {date_filter}
    GROUP BY api_name
    ORDER BY avg_latency DESC
    """
    
    latency_df = db.execute_query_df(latency_query)
    
    if not latency_df.empty and len(latency_df) > 0:
        fig = create_bar_chart(
            latency_df,
            x='api_name',
            y='avg_latency',
            title="Average Latency by API (ms)",
            x_label="API Service",
            y_label="Latency (ms)",
            color='avg_latency'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No latency data available")

with col2:
    
    error_query = f"""
    SELECT 
        api_name,
        AVG(error_rate) as avg_error_rate,
        MAX(error_rate) as max_error_rate,
        COUNT(*) as request_count
    FROM system_reliability sr
    WHERE {system_filter}
    AND {date_filter}
    GROUP BY api_name
    ORDER BY avg_error_rate DESC
    """
    
    error_df = db.execute_query_df(error_query)
    
    if not error_df.empty and len(error_df) > 0:
        fig = create_bar_chart(
            error_df,
            x='api_name',
            y='avg_error_rate',
            title="Average Error Rate by API (%)",
            x_label="API Service",
            y_label="Error Rate (%)",
            color='avg_error_rate'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No error rate data available")

# Second row of charts
col3, col4 = st.columns(2)

with col3:
    
    location_query = f"""
    SELECT 
        location,
        AVG(latency_ms) as avg_latency,
        AVG(reliability_index) as avg_reliability,
        COUNT(*) as request_count
    FROM system_reliability sr
    WHERE {system_filter}
    AND {date_filter}
    AND location IS NOT NULL
    GROUP BY location
    ORDER BY avg_latency DESC
    """
    
    location_df = db.execute_query_df(location_query)
    
    if not location_df.empty and len(location_df) > 0:
        fig = create_bar_chart(
            location_df,
            x='location',
            y='avg_latency',
            title="Average Latency by Location (ms)",
            x_label="Location",
            y_label="Latency (ms)",
            color='avg_latency'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No location data available")

with col4:
    
    severity_query = f"""
    SELECT 
        severity,
        COUNT(*) as incident_count,
        AVG(error_rate) as avg_error_rate
    FROM system_reliability sr
    WHERE {system_filter}
    AND {date_filter}
    GROUP BY severity
    ORDER BY 
        CASE severity
            WHEN 'Critical' THEN 1
            WHEN 'Warning' THEN 2
            WHEN 'Info' THEN 3
        END
    """
    
    severity_df = db.execute_query_df(severity_query)
    
    if not severity_df.empty and len(severity_df) > 0:
        fig = create_bar_chart(
            severity_df,
            x='severity',
            y='incident_count',
            title="Incidents by Severity Level",
            x_label="Severity",
            y_label="Incident Count",
            color='incident_count'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No severity data available")

st.markdown("---")

# ============================================================================
# LATENCY TRENDS OVER TIME
# ============================================================================

st.markdown("### 📅 Latency Trends Over Time")

# Build date filter for system_reliability
sr_date_filter = build_date_filter('sr')

trend_query = f"""
SELECT 
    DATE(sr.timestamp) as date,
    AVG(sr.latency_ms) as avg_latency,
    MAX(sr.latency_ms) as max_latency,
    MIN(sr.latency_ms) as min_latency
FROM system_reliability sr
WHERE {system_filter}
AND {sr_date_filter}
GROUP BY DATE(sr.timestamp)
ORDER BY date
"""

trend_df = db.execute_query_df(trend_query)

if not trend_df.empty and len(trend_df) > 0:
    trend_df['date'] = pd.to_datetime(trend_df['date'])
    
    fig = create_line_chart(
        trend_df,
        x='date',
        y='avg_latency',
        title="Daily Average API Latency",
        x_label="Date",
        y_label="Latency (ms)"
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No trend data available for the selected filters")

st.markdown("---")

# ============================================================================
# ENVIRONMENT QUALITY METRICS
# ============================================================================

st.markdown("### 🌍 Environment Quality Analysis")

col1, col2 = st.columns(2)

with col1:
    
    noise_query = """
    SELECT 
        CASE 
            WHEN noise_level < 40 THEN 'Quiet (0-40 dB)'
            WHEN noise_level < 60 THEN 'Moderate (40-60 dB)'
            WHEN noise_level < 80 THEN 'Noisy (60-80 dB)'
            ELSE 'Very Noisy (80+ dB)'
        END as noise_category,
        COUNT(*) as attempt_count,
        AVG(noise_quality_index) as avg_quality
    FROM environment_metrics
    WHERE noise_level IS NOT NULL
    GROUP BY 
        CASE 
            WHEN noise_level < 40 THEN 'Quiet (0-40 dB)'
            WHEN noise_level < 60 THEN 'Moderate (40-60 dB)'
            WHEN noise_level < 80 THEN 'Noisy (60-80 dB)'
            ELSE 'Very Noisy (80+ dB)'
        END
    ORDER BY 
        CASE 
            WHEN MIN(noise_level) < 40 THEN 1
            WHEN MIN(noise_level) < 60 THEN 2
            WHEN MIN(noise_level) < 80 THEN 3
            ELSE 4
        END
    """
    
    noise_df = db.execute_query_df(noise_query)
    
    if not noise_df.empty and len(noise_df) > 0:
        fig = create_bar_chart(
            noise_df,
            x='noise_category',
            y='attempt_count',
            title="Attempts by Noise Level",
            x_label="Noise Category",
            y_label="Number of Attempts",
            color='attempt_count'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No noise data available")

with col2:
    
    device_query = """
    SELECT 
        device_type,
        AVG(internet_stability_score) as avg_stability,
        AVG(internet_latency_ms) as avg_latency,
        COUNT(*) as attempt_count
    FROM environment_metrics
    WHERE device_type IS NOT NULL
    GROUP BY device_type
    ORDER BY avg_stability DESC
    """
    
    device_df = db.execute_query_df(device_query)
    
    if not device_df.empty and len(device_df) > 0:
        fig = create_bar_chart(
            device_df,
            x='device_type',
            y='avg_stability',
            title="Average Internet Stability by Device Type",
            x_label="Device Type",
            y_label="Stability Score",
            color='avg_stability'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No device data available")

# Third row - connectivity metrics
col5, col6 = st.columns(2)

with col5:
    
    drops_query = """
    SELECT 
        CASE 
            WHEN connection_drops = 0 THEN 'No Drops'
            WHEN connection_drops <= 2 THEN '1-2 Drops'
            WHEN connection_drops <= 5 THEN '3-5 Drops'
            ELSE '6+ Drops'
        END as drop_category,
        COUNT(*) as attempt_count,
        AVG(internet_stability_score) as avg_stability
    FROM environment_metrics
    WHERE connection_drops IS NOT NULL
    GROUP BY 
        CASE 
            WHEN connection_drops = 0 THEN 'No Drops'
            WHEN connection_drops <= 2 THEN '1-2 Drops'
            WHEN connection_drops <= 5 THEN '3-5 Drops'
            ELSE '6+ Drops'
        END
    ORDER BY 
        CASE 
            WHEN MIN(connection_drops) = 0 THEN 1
            WHEN MIN(connection_drops) <= 2 THEN 2
            WHEN MIN(connection_drops) <= 5 THEN 3
            ELSE 4
        END
    """
    
    drops_df = db.execute_query_df(drops_query)
    
    if not drops_df.empty and len(drops_df) > 0:
        fig = create_bar_chart(
            drops_df,
            x='drop_category',
            y='attempt_count',
            title="Attempts by Connection Drop Frequency",
            x_label="Connection Drops",
            y_label="Number of Attempts",
            color='attempt_count'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No connection drop data available")

with col6:
    
    signal_query = """
    SELECT 
        signal_strength,
        COUNT(*) as attempt_count,
        AVG(internet_stability_score) as avg_stability
    FROM environment_metrics
    WHERE signal_strength IS NOT NULL
    GROUP BY signal_strength
    ORDER BY 
        CASE signal_strength
            WHEN 'Excellent' THEN 1
            WHEN 'Good' THEN 2
            WHEN 'Fair' THEN 3
            WHEN 'Poor' THEN 4
            ELSE 5
        END
    """
    
    signal_df = db.execute_query_df(signal_query)
    
    if not signal_df.empty and len(signal_df) > 0:
        fig = create_bar_chart(
            signal_df,
            x='signal_strength',
            y='attempt_count',
            title="Attempts by Signal Strength",
            x_label="Signal Strength",
            y_label="Number of Attempts",
            color='attempt_count'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No signal strength data available")

st.markdown("---")

# ============================================================================
# ENVIRONMENT CORRELATION ANALYSIS
# ============================================================================

st.markdown("### 🔬 Environment Impact on Performance")

correlation_query = """
SELECT 
    em.noise_level,
    em.internet_stability_score,
    em.internet_latency_ms,
    em.connection_drops,
    a.score as student_score
FROM environment_metrics em
INNER JOIN attempts a ON em.attempt_id = a.attempt_id
WHERE em.noise_level IS NOT NULL
AND em.internet_stability_score IS NOT NULL
AND a.score IS NOT NULL
LIMIT 1000
"""

correlation_df = db.execute_query_df(correlation_query)

if not correlation_df.empty and len(correlation_df) > 0:
    col1, col2 = st.columns(2)
    
    with col1:
        fig = create_scatter_plot(
            correlation_df,
            x='noise_level',
            y='student_score',
            title="Noise Level vs Student Performance",
            x_label="Noise Level (dB)",
            y_label="Score (%)",
            color='internet_stability_score',
            size='connection_drops'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = create_scatter_plot(
            correlation_df,
            x='internet_stability_score',
            y='student_score',
            title="Internet Stability vs Student Performance",
            x_label="Stability Score",
            y_label="Score (%)",
            color='noise_level',
            size='connection_drops'
        )
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No correlation data available")

st.markdown("---")

# ============================================================================
# DATA TABLES
# ============================================================================

st.markdown("### 📋 Detailed System Data")

tab1, tab2, tab3, tab4 = st.tabs([
    "🖥️ System Reliability",
    "🌍 Environment Metrics",
    "⚠️ Critical Incidents",
    "📊 Performance Summary"
])

with tab1:
    st.markdown("#### System Reliability Log")
    
    system_table_query = f"""
    SELECT 
        sr.timestamp,
        sr.api_name,
        sr.latency_ms,
        sr.error_rate,
        sr.reliability_index,
        sr.location,
        sr.severity
    FROM system_reliability sr
    WHERE {system_filter}
    AND {date_filter}
    ORDER BY sr.timestamp DESC
    LIMIT 1000
    """
    
    system_table_df = db.execute_query_df(system_table_query)
    
    if not system_table_df.empty:
        system_table_df['timestamp'] = pd.to_datetime(system_table_df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
        system_table_df['latency_ms'] = system_table_df['latency_ms'].apply(
            lambda x: f"{x:.0f} ms" if pd.notna(x) else "N/A"
        )
        system_table_df['error_rate'] = system_table_df['error_rate'].apply(
            lambda x: f"{x:.2f}%" if pd.notna(x) else "N/A"
        )
        system_table_df['reliability_index'] = system_table_df['reliability_index'].apply(
            lambda x: f"{x:.1f}%" if pd.notna(x) else "N/A"
        )
        
        render_data_table(system_table_df, f"system_reliability_{datetime.now().strftime('%Y%m%d')}")
    else:
        st.info("No system reliability data available")

with tab2:
    st.markdown("#### Environment Metrics by Attempt")
    
    env_table_query = """
    SELECT 
        em.attempt_id,
        em.device_type,
        em.microphone_type,
        em.noise_level,
        em.noise_quality_index,
        em.internet_latency_ms,
        em.internet_stability_score,
        em.connection_drops,
        em.signal_strength,
        a.score as student_score
    FROM environment_metrics em
    INNER JOIN attempts a ON em.attempt_id = a.attempt_id
    ORDER BY a.timestamp DESC
    LIMIT 500
    """
    
    env_table_df = db.execute_query_df(env_table_query)
    
    if not env_table_df.empty:
        env_table_df['noise_level'] = env_table_df['noise_level'].apply(
            lambda x: f"{x:.0f} dB" if pd.notna(x) else "N/A"
        )
        env_table_df['internet_latency_ms'] = env_table_df['internet_latency_ms'].apply(
            lambda x: f"{x:.0f} ms" if pd.notna(x) else "N/A"
        )
        env_table_df['student_score'] = env_table_df['student_score'].apply(
            lambda x: f"{x:.1f}%" if pd.notna(x) else "N/A"
        )
        
        render_data_table(env_table_df, f"environment_metrics_{datetime.now().strftime('%Y%m%d')}")
    else:
        st.info("No environment metrics available")

with tab3:
    st.markdown("#### Critical Incidents")
    
    critical_query = f"""
    SELECT 
        sr.timestamp,
        sr.api_name,
        sr.latency_ms,
        sr.error_rate,
        sr.reliability_index,
        sr.location,
        sr.severity
    FROM system_reliability sr
    WHERE sr.severity = 'Critical'
    AND {date_filter}
    ORDER BY sr.timestamp DESC
    LIMIT 200
    """
    
    critical_df = db.execute_query_df(critical_query)
    
    if not critical_df.empty:
        critical_df['timestamp'] = pd.to_datetime(critical_df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
        critical_df['latency_ms'] = critical_df['latency_ms'].apply(
            lambda x: f"{x:.0f} ms" if pd.notna(x) else "N/A"
        )
        critical_df['error_rate'] = critical_df['error_rate'].apply(
            lambda x: f"{x:.2f}%" if pd.notna(x) else "N/A"
        )
        
        st.warning(f"⚠️ {len(critical_df)} critical incident(s) found")
        render_data_table(critical_df, f"critical_incidents_{datetime.now().strftime('%Y%m%d')}")
    else:
        st.success("✅ No critical incidents in the selected time period")

with tab4:
    st.markdown("#### Performance Summary by API")
    
    summary_query = f"""
    SELECT 
        api_name,
        COUNT(*) as total_requests,
        AVG(latency_ms) as avg_latency,
        MIN(latency_ms) as min_latency,
        MAX(latency_ms) as max_latency,
        AVG(error_rate) as avg_error_rate,
        AVG(reliability_index) as avg_reliability,
        COUNT(CASE WHEN severity = 'Critical' THEN 1 END) as critical_count,
        COUNT(CASE WHEN severity = 'Warning' THEN 1 END) as warning_count
    FROM system_reliability sr
    WHERE {system_filter}
    AND {date_filter}
    GROUP BY api_name
    ORDER BY avg_latency DESC
    """
    
    summary_df = db.execute_query_df(summary_query)
    
    if not summary_df.empty:
        summary_df['avg_latency'] = summary_df['avg_latency'].apply(
            lambda x: f"{x:.0f} ms" if pd.notna(x) else "N/A"
        )
        summary_df['min_latency'] = summary_df['min_latency'].apply(
            lambda x: f"{x:.0f} ms" if pd.notna(x) else "N/A"
        )
        summary_df['max_latency'] = summary_df['max_latency'].apply(
            lambda x: f"{x:.0f} ms" if pd.notna(x) else "N/A"
        )
        summary_df['avg_error_rate'] = summary_df['avg_error_rate'].apply(
            lambda x: f"{x:.2f}%" if pd.notna(x) else "N/A"
        )
        summary_df['avg_reliability'] = summary_df['avg_reliability'].apply(
            lambda x: f"{x:.1f}%" if pd.notna(x) else "N/A"
        )
        
        render_data_table(summary_df, f"api_summary_{datetime.now().strftime('%Y%m%d')}")
    else:
        st.info("No summary data available")

st.markdown("---")
st.caption("💡 MIND Unified Dashboard | Miva Open University")
