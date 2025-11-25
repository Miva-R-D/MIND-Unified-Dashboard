from core.db import run_query


# ----------------- BASIC LOADERS -----------------

def load_environment_metrics(start_date=None, end_date=None):
    sql = """
        SELECT *
        FROM environment_metrics
        WHERE attempt_id IN (
            SELECT attempt_id FROM attempts
            WHERE timestamp BETWEEN :start AND :end
        )
        ORDER BY attempt_id;
    """
    return run_query(sql, {
        "start": f"{start_date} 00:00:00",
        "end": f"{end_date} 23:59:59"
    })


def load_environment_for_student(student_id):
    sql = """
        SELECT *
        FROM environment_metrics
        WHERE student_id = :sid
        ORDER BY attempt_id;
    """
    return run_query(sql, {"sid": student_id})


def load_environment_with_attempts(start_date=None, end_date=None):
    """
    Join environment metrics with attempts table for
    correlation plots (e.g., latency vs score).
    """
    sql = """
        SELECT 
            e.*,
            a.score,
            a.timestamp AS attempt_time
        FROM environment_metrics e
        JOIN attempts a
            ON e.attempt_id = a.attempt_id
        WHERE a.timestamp BETWEEN :start AND :end
        ORDER BY a.timestamp;
    """
    return run_query(sql, {
        "start": f"{start_date} 00:00:00",
        "end": f"{end_date} 23:59:59"
    })


# ----------------- AGGREGATES -----------------

def load_environment_summary():
    """
    Basic averages for environment conditions across platform.
    """
    sql = """
        SELECT 
            AVG(noise_level)::numeric(10,2) AS avg_noise,
            AVG(noise_quality_index)::numeric(10,2) AS noise_quality,
            AVG(internet_latency_ms)::numeric(10,2) AS avg_latency,
            AVG(internet_stability_score)::numeric(10,2) AS avg_stability,
            AVG(connection_drops)::numeric(10,2) AS avg_drops
        FROM environment_metrics;
    """
    return run_query(sql)


def load_device_type_distribution():
    sql = """
        SELECT 
            device_type,
            COUNT(*) AS count
        FROM environment_metrics
        GROUP BY device_type
        ORDER BY count DESC;
    """
    return run_query(sql)

