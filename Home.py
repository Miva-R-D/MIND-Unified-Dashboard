"""
MIND Unified Dashboard - Home Page
Main entry point for the multi-page analytics dashboard
"""

import streamlit as st
from auth import init_session_state, login_form, logout, is_authenticated, get_current_user
from theme import COLORS, apply_streamlit_theme
from db import init_database
import base64

# Page configuration
# Try to use logo if available, fallback to emoji
try:
    st.set_page_config(
        page_title="MIND Unified Dashboard",
        page_icon="assets/mind_logo.png",
        layout="wide",
        initial_sidebar_state="expanded"
    )
except:
    st.set_page_config(
        page_title="MIND Unified Dashboard",
        page_icon="💡",
        layout="wide",
        initial_sidebar_state="expanded"
    )

# Apply custom theme
st.markdown(apply_streamlit_theme(), unsafe_allow_html=True)

# Initialize session state
init_session_state()

# Sidebar
with st.sidebar:
    # Logo
    try:
        st.image("assets/mind_logo.png", use_container_width=True)
    except:
        st.markdown("### 🎓 MIVA OPEN UNIVERSITY")
        st.markdown("#### MIND Unified Dashboard")
    
    st.markdown("---")
    
    # Authentication status
    if is_authenticated():
        user = get_current_user()
        st.success(f"👤 **{user['name']}**")
        st.caption(f"Role: {user['role']}")
        
        # Logout button
        if st.button("🚪 Logout", use_container_width=True):
            logout()
    else:
        st.info("Please log in to continue")
    
    st.markdown("---")
    
    # Navigation info
    if is_authenticated():
        st.markdown("### 📊 Available Dashboards")
        user_role = get_current_user()['role']
        
        if user_role == "Admin":
            st.markdown("""
            - 👨‍🎓 Student Dashboard
            - 👩‍🏫 Faculty Dashboard
            - 👨‍💻 Developer Dashboard
            - 🔧 Admin Dashboard
            """)
        elif user_role == "Student":
            st.markdown("- 👨‍🎓 Student Dashboard")
        elif user_role == "Faculty":
            st.markdown("- 👩‍🏫 Faculty Dashboard")
        elif user_role == "Developer":
            st.markdown("- 👨‍💻 Developer Dashboard")
        
        st.caption("Use the sidebar to navigate between dashboards")

# Main content
if not is_authenticated():
    # Login page
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Display logo if available
        try:
            col_logo1, col_logo2, col_logo3 = st.columns([1, 2, 1])
            with col_logo2:
                st.image("assets/mind_logo.png", width=200)
        except:
            pass
        
        st.markdown("# 💡 Welcome to the MIND Unified Dashboard")
        st.markdown("---")
        
        st.markdown("""
        ### A centralized analytics platform for Miva Open University
        
        This platform provides real-time analytics and insights across key domains:
        
        - **Student Performance** 📊
        - **Faculty Cohort Insights** 🎓  
        - **System Reliability & Environment Quality** 💻
        - **Institution-wide Administrative KPIs** 📈
        
        Please log in to access your dashboard.
        """)
        
        st.markdown("---")
        
        # Login form
        login_form()
        
else:
    # Home page for authenticated users
    user = get_current_user()
    
    # Welcome header with logo
    col_header1, col_header2 = st.columns([1, 6])
    with col_header1:
        try:
            st.image("assets/mind_logo.png", width=100)
        except:
            st.markdown("# 💡")
    with col_header2:
        st.markdown(f"# Welcome to the MIND Unified Dashboard")
        st.markdown(f"### Hello {user['name']} 👋")
    
    st.markdown("---")
    
    # Role-specific welcome message
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown(f"**Your current access role:** {user['role']}")
        
        st.markdown("""
        This platform provides real-time analytics and insights across key domains:
        
        - **Student Performance** 📊
        - **Faculty Cohort Insights** 🎓  
        - **System Reliability & Environment Quality** 💻
        - **Institution-wide Administrative KPIs** 📈
        
        Please use the sidebar on the left to navigate to the dashboards available to your role.
        """)
    
    with col2:
        # Quick stats card
        st.markdown(f"""
        <div style="
            background-color: {COLORS['white']};
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-left: 4px solid {COLORS['primary']};
        ">
            <h4 style="color: {COLORS['primary']}; margin-top: 0;">Your Access</h4>
            <p><strong>Role:</strong> {user['role']}</p>
            <p><strong>Email:</strong> {user['email']}</p>
            {f"<p><strong>Student ID:</strong> {user['student_id']}</p>" if user.get('student_id') else ""}
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Available dashboards section
    st.markdown("## 📊 Your Dashboards")
    
    if user['role'] == "Admin":
        st.info("✨ You have access to **all dashboards** listed in the sidebar.")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div style="
                background-color: {COLORS['white']};
                border-radius: 10px;
                padding: 20px;
                text-align: center;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            ">
                <h2 style="color: {COLORS['primary']}; margin: 0;">👨‍🎓</h2>
                <h4 style="margin: 10px 0;">Student</h4>
                <p style="font-size: 0.9rem; color: {COLORS['text_light']};">
                    Performance tracking, rubric scores, engagement
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style="
                background-color: {COLORS['white']};
                border-radius: 10px;
                padding: 20px;
                text-align: center;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            ">
                <h2 style="color: {COLORS['primary']}; margin: 0;">👩‍🏫</h2>
                <h4 style="margin: 10px 0;">Faculty</h4>
                <p style="font-size: 0.9rem; color: {COLORS['text_light']};">
                    Cohort analytics, at-risk students, rubric mastery
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div style="
                background-color: {COLORS['white']};
                border-radius: 10px;
                padding: 20px;
                text-align: center;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            ">
                <h2 style="color: {COLORS['primary']}; margin: 0;">👨‍💻</h2>
                <h4 style="margin: 10px 0;">Developer</h4>
                <p style="font-size: 0.9rem; color: {COLORS['text_light']};">
                    System health, API performance, environment quality
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div style="
                background-color: {COLORS['white']};
                border-radius: 10px;
                padding: 20px;
                text-align: center;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            ">
                <h2 style="color: {COLORS['accent']}; margin: 0;">🔧</h2>
                <h4 style="margin: 10px 0;">Admin</h4>
                <p style="font-size: 0.9rem; color: {COLORS['text_light']};">
                    Platform-wide KPIs, trends, cross-cutting analytics
                </p>
            </div>
            """, unsafe_allow_html=True)
    
    elif user['role'] == "Student":
        st.markdown(f"""
        <div style="
            background-color: {COLORS['white']};
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-left: 4px solid {COLORS['primary']};
        ">
            <h3 style="color: {COLORS['primary']}; margin-top: 0;">👨‍🎓 Student Dashboard</h3>
            <p>Track your performance, view rubric feedback, monitor your engagement, and see your progress over time.</p>
            <ul>
                <li>View your scores and improvement trends</li>
                <li>See detailed rubric feedback</li>
                <li>Monitor your engagement and time on task</li>
                <li>Review environment quality during attempts</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    elif user['role'] == "Faculty":
        st.markdown(f"""
        <div style="
            background-color: {COLORS['white']};
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-left: 4px solid {COLORS['primary']};
        ">
            <h3 style="color: {COLORS['primary']}; margin-top: 0;">👩‍🏫 Faculty Dashboard</h3>
            <p>Monitor cohort performance, identify at-risk students, and analyze rubric mastery patterns.</p>
            <ul>
                <li>View cohort-wide performance metrics</li>
                <li>Identify students who need support</li>
                <li>Analyze rubric dimension mastery</li>
                <li>Track engagement and completion rates</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    elif user['role'] == "Developer":
        st.markdown(f"""
        <div style="
            background-color: {COLORS['white']};
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-left: 4px solid {COLORS['primary']};
        ">
            <h3 style="color: {COLORS['primary']}; margin-top: 0;">👨‍💻 Developer Dashboard</h3>
            <p>Monitor system health, API performance, and environment quality metrics.</p>
            <ul>
                <li>Track API latency and reliability</li>
                <li>Monitor environment quality impact</li>
                <li>Identify critical incidents</li>
                <li>Analyze device and connectivity patterns</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Getting started section
    with st.expander("💡 Getting Started", expanded=False):
        st.markdown("""
        ### How to use this dashboard:
        
        1. **Navigate** using the sidebar on the left
        2. **Select** the dashboard relevant to your role
        3. **Use filters** to narrow down the data you want to view
        4. **Interact** with charts and tables for detailed insights
        5. **Export** data tables when needed
        
        ### Need help?
        
        - Each dashboard has specific filters and controls
        - Hover over charts for detailed information
        - Use date range filters to focus on specific time periods
        - Contact support if you encounter any issues
        """)
    
    # Database connection test
    try:
        db = init_database()
        st.success("✅ Database connection established")
    except Exception as e:
        st.error(f"⚠️ Database connection issue: {str(e)}")
        st.info("""
        Please ensure your database connection is properly configured in `.streamlit/secrets.toml`
        """)
