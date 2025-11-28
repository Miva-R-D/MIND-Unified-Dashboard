import pandas as pd
from typing import Optional
# Assuming db.py is one level up (in core/)
from db import run_query 


# ----------------- BASIC ENGAGEMENT LOADERS -----------------

def load_engagement_logs(start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
    """Load all engagement logs with optional date filtering."""
    
    # Base SQL query structure
    sql = """
        SELECT *
        FROM engagement_logs
        WHERE timestamp >= :start AND timestamp <= :end
        ORDER BY timestamp;
    """
    
    # Prepare parameters with safe default date range
    params = {
        # Using YYYY-MM-DD strings for consistency. 
        # The inclusion of time ensures the full day is captured.
        "start": f"{start_date} 00:00:00" if start_date else "1900-01-01 00:00:00",
        "end": f"{end_date} 23:59:59" if end_date else "2999-12-31 23:59:59"
    }
    
    return run_query(sql, params)


def load_engagement_for_student(student_id: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
    """Load engagement logs for a specific student with optional date filtering."""
    
    sql = """
        SELECT *
        FROM engagement_logs
        WHERE student_id = :sid
        AND timestamp >= :start AND timestamp <= :end
        ORDER BY timestamp;
    """
    
    # Prepare parameters with safe default date range
    params = {
        "sid": student_id,
        "start": f"{start_date} 00:00:00" if start_date else "1900-01-01 00:00:00",
        "end": f"{end_date} 23:59:59" if end_date else "2999-12-31 23:59:59"
    }
    
    return run_query(sql, params)


# ----------------- AGGREGATES -----------------

def load_daily_engagement() -> pd.DataFrame:
    """
    For time-series charts: calculate the number of engagement logs per day.
    """
    sql = """
        SELECT 
            -- Casting to DATE truncates the timestamp to the day
            DATE(timestamp) AS day,
            COUNT(*) AS events,
            SUM(duration_seconds) AS total_duration_daily
        FROM engagement_logs
        GROUP BY DATE(timestamp)
        ORDER BY day;
    """
    # Added SUM(duration_seconds) as it's often useful alongside event count
    return run_query(sql)


def load_total_engagement_per_student() -> pd.DataFrame:
    """
    Total engagement duration for each student.
    """
    sql = """
        SELECT 
            student_id,
            SUM(duration_seconds)::numeric(10,2) AS total_duration_seconds,
            COUNT(DISTINCT DATE(timestamp)) AS days_engaged
        FROM engagement_logs
        GROUP BY student_id
        ORDER BY total_duration_seconds DESC;
    """
    # Added a CAST for cleaner output and 'days_engaged' for a richer metric
    return run_query(sql)


def load_engagement_per_case() -> pd.DataFrame:
    """
    Engagement time grouped by case study.
    """
    sql = """
        SELECT 
            case_id,
            SUM(duration_seconds)::numeric(10,2) AS total_time_seconds,
            COUNT(DISTINCT student_id) AS distinct_users
        FROM engagement_logs
        GROUP BY case_id
        ORDER BY total_time_seconds DESC;
    """
    # Added 'distinct_users' and ordered by time for bar charts
    return run_query(sql)
