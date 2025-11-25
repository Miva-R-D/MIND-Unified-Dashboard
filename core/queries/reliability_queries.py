from core.db import run_query


# ----------------- BASIC LOADERS -----------------

def load_system_reliability(start_date=None, end_date=None):
    """
    Full reliability logs filtered by date.
    """
    sql = """
        SELECT *
        FROM system_reliability
        WHERE timestamp BETWEEN :start AND :end
        ORDER BY timestamp;
    """
    return run_query(sql, {
        "start": f"{start_date} 00:00:00",
        "end": f"{end_date} 23:59:59"
    })


def load_latest_reliability():
    """
    Latest reliability readings (useful for KPI tiles).
    """
    sql = """
        SELECT *
        FROM system_reliability
        ORDER BY timestamp DESC
        LIMIT 20;
    """
    return run_query(sql)


# ----------------- AGGREGATES -----------------

def load_api_latency_summary():
    sql = """
        SELECT
            api_name,
            AVG(latency_ms)::numeric(10,2) AS avg_latency,
            PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY latency_ms) AS p50,
            PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_ms) AS p95
        FROM system_reliability
        GROUP BY api_name
        ORDER BY api_name;
    """
    return run_query(sql)


def load_error_rate_by_api():
    sql = """
        SELECT
            api_name,
            AVG(error_rate)::numeric(10,4) AS avg_error
        FROM system_reliability
        GROUP BY api_name
        ORDER BY avg_error DESC;
    """
    return run_query(sql)


def load_critical_incidents():
    sql = """
        SELECT *
        FROM system_reliability
        WHERE severity = 'Critical'
        ORDER BY timestamp DESC;
    """
    return run_query(sql)


def load_incidents_by_location():
    sql = """
        SELECT 
            location,
            COUNT(*) AS incidents
        FROM system_reliability
        WHERE severity = 'Critical'
        GROUP BY location
        ORDER BY incidents DESC;
    """
    return run_query(sql)

