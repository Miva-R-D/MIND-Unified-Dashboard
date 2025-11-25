from core.db import run_query


# ------------------ ADMIN AGGREGATES TABLE ------------------

def load_admin_aggregates(start_date=None, end_date=None):
    """
    Load metrics from admin_aggregates table.
    """
    sql = """
        SELECT *
        FROM admin_aggregates
        WHERE timestamp BETWEEN :start AND :end
        ORDER BY timestamp;
    """
    return run_query(sql, {
        "start": f"{start_date} 00:00:00",
        "end": f"{end_date} 23:59:59"
    })


def load_admin_metrics_over_time(metric_name):
    """
    Trend for a specific admin metric.
    """
    sql = """
        SELECT timestamp, metric_value
        FROM admin_aggregates
        WHERE metric_name = :m
        ORDER BY timestamp;
    """
    return run_query(sql, {"m": metric_name})


# ------------------ GLOBAL SUMMARIES ------------------

def total_active_students(start_date=None, end_date=None):
    sql = """
        SELECT COUNT(DISTINCT student_id) AS active_students
        FROM attempts
        WHERE timestamp BETWEEN :start AND :end;
    """
    return run_query(sql, {
        "start": f"{start_date} 00:00:00",
        "end": f"{end_date} 23:59:59"
    })


def total_attempts(start_date=None, end_date=None):
    sql = """
        SELECT COUNT(*) AS attempts_count
        FROM attempts
        WHERE timestamp BETWEEN :start AND :end;
    """
    return run_query(sql, {
        "start": f"{start_date} 00:00:00",
        "end": f"{end_date} 23:59:59"
    })


def average_score(start_date=None, end_date=None):

