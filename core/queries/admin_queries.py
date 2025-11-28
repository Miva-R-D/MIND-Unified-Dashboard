import pandas as pd
from typing import Optional
# Assuming db.py is one level up (in core/)
from db import run_query 


# ------------------ ADMIN AGGREGATES TABLE ------------------

def load_admin_aggregates(start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
    """
    Load metrics from the pre-computed admin_aggregates table, filtered by date.
    """
    sql = """
        SELECT *
        FROM admin_aggregates
        WHERE timestamp >= :start AND timestamp <= :end
        ORDER BY timestamp;
    """
    
    # Prepare parameters with safe default date range
    params = {
        "start": f"{start_date} 00:00:00" if start_date else "1900-01-01 00:00:00",
        "end": f"{end_date} 23:59:59" if end_date else "2999-12-31 23:59:59"
    }
    
    return run_query(sql, params)


def load_admin_metrics_over_time(metric_name: str) -> pd.DataFrame:
    """
    Trend for a specific admin metric from the aggregates table.
    (Assumes filtering is handled by the initial aggregate load or is not needed here).
    """
    sql = """
        SELECT timestamp, metric_value
        FROM admin_aggregates
        WHERE metric_name = :m
        ORDER BY timestamp;
    """
    return run_query(sql, {"m": metric_name})


# ------------------ GLOBAL SUMMARIES (Live Queries) ------------------

def total_active_students(start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
    """
    Count the number of unique students who recorded an attempt in the period.
    """
    sql = """
        SELECT COUNT(DISTINCT student_id) AS active_students
        FROM attempts
        WHERE timestamp >= :start AND timestamp <= :end;
    """
    
    # Prepare parameters with safe default date range
    params = {
        "start": f"{start_date} 00:00:00" if start_date else "1900-01-01 00:00:00",
        "end": f"{end_date} 23:59:59" if end_date else "2999-12-31 23:59:59"
    }
    
    return run_query(sql, params)


def total_attempts(start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
    """
    Count the total number of attempts recorded in the period.
    """
    sql = """
        SELECT COUNT(*) AS attempts_count
        FROM attempts
        WHERE timestamp >= :start AND timestamp <= :end;
    """
    
    # Prepare parameters with safe default date range
    params = {
        "start": f"{start_date} 00:00:00" if start_date else "1900-01-01 00:00:00",
        "end": f"{end_date} 23:59:59" if end_date else "2999-12-31 23:59:59"
    }
    
    return run_query(sql, params)


def average_score(start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
    """
    Calculate the average overall score across all attempts in the period.
    """
    sql = """
        SELECT 
            AVG(score)::numeric(10,2) AS avg_score,
            AVG(duration_seconds)::numeric(10,2) AS avg_duration
        FROM attempts
        WHERE timestamp >= :start AND timestamp <= :end;
    """
    
    # Prepare parameters with safe default date range
    params = {
        "start": f"{start_date} 00:00:00" if start_date else "1900-01-01 00:00:00",
        "end": f"{end_date} 23:59:59" if end_date else "2999-12-31 23:59:59"
    }
    
    return run_query(sql, params)


# ------------------ MISSING FACULTY/ADMIN SUMMARIES ------------------

def case_study_summary(start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
    """
    Summary of performance metrics per case study, filtered by date.
    """
    sql = """
        SELECT
            a.case_id,
            COUNT(a.attempt_id) AS total_attempts,
            COUNT(DISTINCT a.student_id) AS total_students,
            AVG(a.score)::numeric(10,2) AS avg_score,
            AVG(a.duration_seconds)::numeric(10,2) AS avg_duration_sec
        FROM attempts a
        WHERE a.timestamp >= :start AND a.timestamp <= :end
        GROUP BY a.case_id
        ORDER BY avg_score DESC;
    """
    params = {
        "start": f"{start_date} 00:00:00" if start_date else "1900-01-01 00:00:00",
        "end": f"{end_date} 23:59:59" if end_date else "2999-12-31 23:59:59"
    }
    return run_query(sql, params)


def campus_summary() -> pd.DataFrame:
    """
    Loads global aggregate campus performance metrics (assumed pre-computed or joined).
    Since no date filter is passed in the dashboard, this loads the current global state.
    Assumes a pre-computed table named 'campus_metrics' or similar.
    """
    sql = """
        SELECT 
            campus_name, 
            avg_score::numeric(10,2), 
            active_students, 
            last_updated 
        FROM campus_metrics
        ORDER BY active_students DESC;
    """
    # NOTE: This query does not use date filters as the Faculty Dashboard called it without them.
    return run_query(sql)


def department_summary() -> pd.DataFrame:
    """
    Loads global aggregate department performance metrics. 
    Assumes a pre-computed table named 'department_metrics'.
    """
    sql = """
        SELECT 
            department_name, 
            avg_mastery::numeric(10,4), 
            total_students, 
            last_updated 
        FROM department_metrics
        ORDER BY avg_mastery DESC;
    """
    # NOTE: This query does not use date filters as the Faculty Dashboard called it without them.
    return run_query(sql)
