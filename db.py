"""
Database connection manager for MIND Unified Dashboard
Handles Neon Postgres connections securely
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
import streamlit as st
from typing import List, Dict, Any, Optional
import pandas as pd

class DatabaseManager:
    """Manages database connections and query execution"""
    
    def __init__(self):
        """Initialize database connection from Streamlit secrets or environment variables"""
        self.connection_params = self._get_connection_params()
        self.conn = None
        
    def _get_connection_params(self) -> Dict[str, str]:
        """
        Get database connection parameters from Streamlit secrets or environment
        
        Priority:
        1. Streamlit secrets (for deployment)
        2. Environment variables (for local development)
        """
        try:
            # Try Streamlit secrets first
            params = {
                'host': st.secrets["database"]["host"],
                'database': st.secrets["database"]["database"],
                'user': st.secrets["database"]["user"],
                'password': st.secrets["database"]["password"],
                'port': st.secrets["database"].get("port", 5432),
                'sslmode': st.secrets["database"].get("sslmode", "require")
            }
            
            # DEBUG: Show what was loaded
            st.write("✅ DEBUG: Successfully loaded Streamlit secrets")
            st.write(f"📍 DEBUG: Host = {params['host']}")
            st.write(f"📍 DEBUG: Database = {params['database']}")
            
            return params
            
        except (KeyError, FileNotFoundError) as e:
            # DEBUG: Show error
            st.error(f"❌ DEBUG: Failed to load secrets - {e}")
            st.warning("⚠️ DEBUG: Falling back to environment variables")
            
            # Fall back to environment variables
            return {
                'host': os.getenv('DB_HOST'),
                'database': os.getenv('DB_NAME'),
                'user': os.getenv('DB_USER'),
                'password': os.getenv('DB_PASSWORD'),
                'port': os.getenv('DB_PORT', 5432),
                'sslmode': os.getenv('DB_SSLMODE', 'require')
            }
    
    def get_connection(self):
        """Get or create database connection"""
        try:
            if self.conn is None or self.conn.closed:
                self.conn = psycopg2.connect(**self.connection_params)
            return self.conn
        except psycopg2.Error as e:
            st.error(f"Database connection error: {e}")
            return None
    
    def execute_query(self, query: str, params: tuple = None) -> Optional[List[Dict[str, Any]]]:
        """
        Execute a SELECT query and return results as list of dictionaries
        
        Args:
            query: SQL query string
            params: Query parameters (for parameterized queries)
            
        Returns:
            List of dictionaries with query results, or None if error
        """
        try:
            conn = self.get_connection()
            if conn is None:
                return None
                
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                results = cursor.fetchall()
                # Convert RealDictRow to regular dict
                return [dict(row) for row in results]
                
        except psycopg2.Error as e:
            st.error(f"Query execution error: {e}")
            return None
    
    def execute_query_df(self, query: str, params: tuple = None) -> Optional[pd.DataFrame]:
        """
        Execute a SELECT query and return results as pandas DataFrame
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            pandas DataFrame with query results, or empty DataFrame if error
        """
        try:
            conn = self.get_connection()
            if conn is None:
                return pd.DataFrame()
                
            df = pd.read_sql_query(query, conn, params=params)
            return df
            
        except (psycopg2.Error, pd.io.sql.DatabaseError) as e:
            st.error(f"Query execution error: {e}")
            return pd.DataFrame()
    
    def execute_write(self, query: str, params: tuple = None) -> bool:
        """
        Execute an INSERT, UPDATE, or DELETE query
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self.get_connection()
            if conn is None:
                return False
                
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                conn.commit()
                return True
                
        except psycopg2.Error as e:
            st.error(f"Write operation error: {e}")
            if self.conn:
                self.conn.rollback()
            return False
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            conn = self.get_connection()
            if conn is None:
                return False
                
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1;")
                result = cursor.fetchone()
                return result[0] == 1
                
        except psycopg2.Error:
            return False
    
    def close(self):
        """Close database connection"""
        if self.conn and not self.conn.closed:
            self.conn.close()


# Global database manager instance
@st.cache_resource
def get_db_manager():
    """Get cached database manager instance"""
    return DatabaseManager()


def init_database():
    """
    Initialize database connection and verify it's working
    Should be called at the start of each page
    """
    db = get_db_manager()
    
    if not db.test_connection():
        st.error("⚠️ Unable to connect to database. Please check your connection settings.")
        st.info("""
        **Setup Instructions:**
        
        1. Create a `.streamlit/secrets.toml` file with:
```toml
        [database]
        host = "your-neon-host.neon.tech"
        database = "your-database-name"
        user = "your-username"
        password = "your-password"
        port = 5432
        sslmode = "require"
```
        
        2. Or set environment variables:
        - DB_HOST
        - DB_NAME
        - DB_USER
        - DB_PASSWORD
        """)
        st.stop()
    
    return db
