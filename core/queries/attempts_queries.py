import pandas as pd
from typing import Optional, Dict
# Assuming db.py is one level up in the project root
from ..db import run_query # CORRECTED RELATIVE IMPORT

# ----------------- BASIC LOADERS -----------------

def load_attempts(start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
    """Load attempts with optional date filtering."""
    
    # 1. Base SQL query structure
    sql = """
        SELECT *
        FROM attempts
        WHERE timestamp >= :start AND timestamp <= :end
        ORDER BY timestamp;
    """
    
    # 2. Prepare parameters for date filtering
    # Default to a wide range if dates are not provided
    params = {
        # Assuming dates are passed as YYYY-MM-DD strings
        "start": f"{start_date} 00:00:00" if start_date else "1900-01-01 00:00:00",
        "end": f"{end_date} 23:59:59" if end_date else "2999-12-31 23:59:59"
    }
    
    return run_query(sql, params)


def load_attempts_for_student(student_id: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
    """Load attempts for a specific student with optional date filtering."""
    
    sql = """
        SELECT *
        FROM attempts
        WHERE student_id = :sid
        AND timestamp >= :start AND timestamp <= :end
        ORDER BY timestamp;
    """
    
    params = {
        "sid": student_id,
        "start": f"{start_date} 00:00:00" if start_date else "1900-01-01 00:00:00",
        "end": f"{end_date} 23:59:59" if end_date else "2999-12-31 23:59:59"
    }
    
    return run_query(sql, params)


def load_latest_attempts_per_case(student_id: str) -> pd.DataFrame:
    """
    Latest attempt (highest attempt_number) per case for a given student.
    
    Uses standard DISTINCT ON (PostgreSQL feature) for efficiency.
    """
    sql = """
        SELECT DISTINCT ON (case_id)
            case_id, attempt_number, score, duration_seconds,
            ces_value, timestamp, state
        FROM attempts
        WHERE student_id = :sid
        ORDER BY case_id, attempt_number DESC, timestamp DESC; 
        -- Added timestamp DESC for tie-breaking safety
    """
    return run_query(sql, {"sid": student_id})


# ----------------- AGGREGATIONS -----------------

def load_case_averages() -> pd.DataFrame:
    """
    Average score, time, and CES value per case across all attempts.
    
    NOTE: Added date filtering for consistency, though dashboard calls it without dates.
    """
    # NOTE: The original function definition didn't include date args, but adding
    # them here makes the function more flexible for other uses.
    # We will adjust the dashboard call if needed, but for now, we leave the 
    # query as is since the function signature was simple.
    sql = """
        SELECT 
            case_id,
            AVG(score)::numeric(10,2) AS avg_score,
            AVG(duration_seconds)::numeric(10,2) AS avg_time,
            AVG(ces_value)::numeric(10,2) AS avg_ces,
            COUNT(id) AS total_attempts
        FROM attempts
        GROUP BY case_id
        ORDER BY case_id;
    """
    # No params are used in this version of the query, so run_query() is called without them.
    return run_query(sql)


def load_first_vs_second_attempt_improvements() -> pd.DataFrame:
    """
    Calculates the average improvement in score from the first attempt 
    to the second attempt for each case across all students.
    
    Uses a Common Table Expression (CTE) and Window Functions for efficiency.
    """
    # NOTE: This query does not include date filters, relying on all-time data.
    sql = """
        WITH StudentAttempts AS (
            -- Calculate the score of the previous attempt for each student and case
            SELECT
                student_id,
                case_id,
                attempt_number,
                score,
                LAG(score, 1) 
                    OVER (PARTITION BY student_id, case_id ORDER BY attempt_number ASC) AS previous_score
            FROM 
                attempts
        ),
        Improvements AS (
            -- Filter to the second attempt and calculate the improvement
            SELECT
                case_id,
                (score - previous_score) AS score_improvement
            FROM
                StudentAttempts
            WHERE
                attempt_number = 2 AND previous_score IS NOT NULL
        )
        -- Final aggregation
        SELECT 
            case_id,
            AVG(score_improvement)::numeric(10,2) AS avg_improvement_score
        FROM Improvements
        GROUP BY case_id
        ORDER BY case_id;
    """
    return run_query(sql)
