"""
Authentication module for MIND Unified Dashboard
Handles user login and role-based access control
"""

import streamlit as st
from typing import Optional, Dict
from db import get_db_manager

# Default credentials (for demo/initial setup)
# In production, these should be stored in database with hashed passwords
DEFAULT_USERS = {
    'admin@example.com': {
        'password': 'admin123',  # Change this!
        'role': 'Admin',
        'name': 'Administrator'
    },
    'student@example.com': {
        'password': 'student123',
        'role': 'Student',
        'name': 'Demo Student',
        'student_id': 'STU001'
    },
    'faculty@example.com': {
        'password': 'faculty123',
        'role': 'Faculty',
        'name': 'Demo Faculty'
    },
    'developer@example.com': {
        'password': 'dev123',
        'role': 'Developer',
        'name': 'Demo Developer'
    }
}

def init_session_state():
    """Initialize session state variables"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_email' not in st.session_state:
        st.session_state.user_email = None
    if 'user_role' not in st.session_state:
        st.session_state.user_role = None
    if 'user_name' not in st.session_state:
        st.session_state.user_name = None
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None

def authenticate_user(email: str, password: str) -> Optional[Dict]:
    """
    Authenticate user credentials
    
    Args:
        email: User email
        password: User password
        
    Returns:
        User data dictionary if authenticated, None otherwise
    """
    # First check default users (demo purposes)
    if email in DEFAULT_USERS:
        user = DEFAULT_USERS[email]
        if user['password'] == password:
            return {
                'email': email,
                'name': user['name'],
                'role': user['role'],
                'student_id': user.get('student_id')
            }
    
    # TODO: Add database authentication for production
    # db = get_db_manager()
    # query = """
    #     SELECT student_id, name, role 
    #     FROM students 
    #     WHERE email = %s AND password_hash = crypt(%s, password_hash)
    # """
    # result = db.execute_query(query, (email, password))
    
    return None

def login_form():
    """Display login form"""
    st.markdown("### 🔐 Login to MIND Dashboard")
    
    with st.form("login_form"):
        email = st.text_input("Email", placeholder="your.email@example.com")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login", use_container_width=True)
        
        if submit:
            if not email or not password:
                st.error("Please enter both email and password")
                return
            
            user = authenticate_user(email, password)
            
            if user:
                st.session_state.authenticated = True
                st.session_state.user_email = user['email']
                st.session_state.user_role = user['role']
                st.session_state.user_name = user['name']
                st.session_state.user_id = user.get('student_id')
                st.success(f"Welcome, {user['name']}!")
                st.rerun()
            else:
                st.error("Invalid credentials. Please try again.")
    
    # Demo credentials info
    with st.expander("📋 Demo Credentials"):
        st.markdown("""
        **Admin Access:**
        - Email: `admin@example.com`
        - Password: `admin123`
        
        **Student Access:**
        - Email: `student@example.com`
        - Password: `student123`
        
        **Faculty Access:**
        - Email: `faculty@example.com`
        - Password: `faculty123`
        
        **Developer Access:**
        - Email: `developer@example.com`
        - Password: `dev123`
        """)

def logout():
    """Log out the current user"""
    st.session_state.authenticated = False
    st.session_state.user_email = None
    st.session_state.user_role = None
    st.session_state.user_name = None
    st.session_state.user_id = None
    st.rerun()

def require_auth(allowed_roles: list = None):
    """
    Decorator/function to require authentication for a page
    
    Args:
        allowed_roles: List of roles allowed to access the page
                      If None, any authenticated user can access
    """
    init_session_state()
    
    if not st.session_state.authenticated:
        st.warning("⚠️ Please log in to access this page")
        login_form()
        st.stop()
    
    if allowed_roles and st.session_state.user_role not in allowed_roles:
        st.error(f"⛔ Access Denied: This page requires {' or '.join(allowed_roles)} role")
        st.info(f"Your current role: **{st.session_state.user_role}**")
        st.stop()

def get_current_user():
    """Get current logged-in user information"""
    return {
        'email': st.session_state.user_email,
        'name': st.session_state.user_name,
        'role': st.session_state.user_role,
        'student_id': st.session_state.user_id
    }

def is_authenticated() -> bool:
    """Check if user is authenticated"""
    return st.session_state.get('authenticated', False)

def has_role(role: str) -> bool:
    """Check if current user has specific role"""
    return st.session_state.get('user_role') == role

def get_student_id() -> Optional[str]:
    """Get current student ID (if logged in as student)"""
    return st.session_state.get('user_id')
