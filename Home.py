"""
MIND Unified Dashboard - Home Page
Main entry point for the multi-page analytics dashboard
"""

import streamlit as st
from auth import init_session_state, login_form, logout, is_authenticated, get_current_user
from theme import COLORS, apply_streamlit_theme
from db import init_database
import base64

"""
Dynamic Theme System for MIND Dashboard
Provides light/dark mode toggle across all pages
"""

import streamlit as st

# Initialize theme in session state
def init_theme():
    """Initialize theme state if not exists"""
    if "theme" not in st.session_state:
        st.session_state.theme = "light"  # Default to light mode

def get_theme():
    """Get current theme"""
    return st.session_state.get("theme", "light")

def toggle_theme():
    """Toggle between light and dark mode"""
    st.session_state.theme = "dark" if st.session_state.theme == "light" else "light"

# Theme CSS configurations
LIGHT_THEME = """
<style>
    /* Main background */
    .stApp {
        background-color: #FFFFFF;
        color: #262730;
    }
    
    /* Content area */
    .block-container {
        background-color: #FFFFFF;
        color: #262730;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #F0F2F6;
        color: #262730;
    }
    
    [data-testid="stSidebar"] .css-1d391kg {
        color: #262730;
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        color: #262730;
    }
    
    [data-testid="stMetricLabel"] {
        color: #595959;
    }
    
    /* Headers */
    h1, h2, h3, h4, h5, h6 {
        color: #262730 !important;
    }
    
    /* Text */
    p, span, div {
        color: #262730;
    }
    
    /* Cards/containers */
    div[data-testid="stVerticalBlock"] > div {
        background-color: #FFFFFF;
    }
    
    /* Input fields */
    input, textarea, select {
        background-color: #FFFFFF !important;
        color: #262730 !important;
        border: 1px solid #E0E0E0 !important;
    }
    
    /* Buttons */
    .stButton > button {
        background-color: #800020;
        color: #FFFFFF;
        border: none;
    }
    
    .stButton > button:hover {
        background-color: #600018;
    }
    
    /* Dataframes */
    .dataframe {
        background-color: #FFFFFF !important;
        color: #262730 !important;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background-color: #F0F2F6;
        color: #262730;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #F0F2F6;
    }
    
    .stTabs [data-baseweb="tab"] {
        color: #262730;
    }
    
    /* Success/Info/Warning boxes */
    .stSuccess, .stInfo, .stWarning, .stError {
        background-color: #F0F2F6;
        color: #262730;
    }
</style>
"""

DARK_THEME = """
<style>
    /* Main background */
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    
    /* Content area */
    .block-container {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #262730;
        color: #FAFAFA;
    }
    
    [data-testid="stSidebar"] .css-1d391kg {
        color: #FAFAFA;
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        color: #FAFAFA;
    }
    
    [data-testid="stMetricLabel"] {
        color: #BDBDBD;
    }
    
    /* Headers */
    h1, h2, h3, h4, h5, h6 {
        color: #FAFAFA !important;
    }
    
    /* Text */
    p, span, div {
        color: #FAFAFA;
    }
    
    /* Cards/containers */
    div[data-testid="stVerticalBlock"] > div {
        background-color: #1E1E1E;
    }
    
    /* Input fields */
    input, textarea, select {
        background-color: #262730 !important;
        color: #FAFAFA !important;
        border: 1px solid #4A4A4A !important;
    }
    
    /* Buttons */
    .stButton > button {
        background-color: #800020;
        color: #FFFFFF;
        border: none;
    }
    
    .stButton > button:hover {
        background-color: #A00028;
    }
    
    /* Dataframes */
    .dataframe {
        background-color: #1E1E1E !important;
        color: #FAFAFA !important;
    }
    
    .dataframe thead th {
        background-color: #262730 !important;
        color: #FAFAFA !important;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background-color: #262730;
        color: #FAFAFA;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #262730;
    }
    
    .stTabs [data-baseweb="tab"] {
        color: #FAFAFA;
    }
    
    /* Success/Info/Warning boxes */
    .stSuccess {
        background-color: #1B4332;
        color: #FAFAFA;
    }
    
    .stInfo {
        background-color: #1E3A5F;
        color: #FAFAFA;
    }
    
    .stWarning {
        background-color: #5F3A1E;
        color: #FAFAFA;
    }
    
    .stError {
        background-color: #5F1E1E;
        color: #FAFAFA;
    }
    
    /* Plotly charts background */
    .js-plotly-plot .plotly {
        background-color: transparent !important;
    }
</style>
"""

def apply_theme():
    """Apply current theme CSS"""
    init_theme()
    theme = get_theme()
    
    if theme == "dark":
        st.markdown(DARK_THEME, unsafe_allow_html=True)
    else:
        st.markdown(LIGHT_THEME, unsafe_allow_html=True)

def create_theme_toggle():
    """Create theme toggle widget"""
    init_theme()
    
    # Create toggle in sidebar
    current_theme = get_theme()
    
    col1, col2 = st.sidebar.columns([3, 1])
    
    with col1:
        st.sidebar.markdown("### 🎨 Theme")
    
    with col2:
        # Toggle button
        is_dark = st.sidebar.toggle(
            "Dark",
            value=(current_theme == "dark"),
            key="theme_toggle",
            help="Toggle between light and dark mode"
        )
        
        # Update theme based on toggle
        new_theme = "dark" if is_dark else "light"
        
        if new_theme != st.session_state.theme:
            st.session_state.theme = new_theme
            st.rerun()

def get_plotly_theme():
    """Get Plotly theme configuration based on current theme"""
    theme = get_theme()
    
    if theme == "dark":
        return {
            'layout': {
                'paper_bgcolor': '#0E1117',
                'plot_bgcolor': '#0E1117',
                'font': {'color': '#FAFAFA'},
                'xaxis': {
                    'gridcolor': '#262730',
                    'zerolinecolor': '#262730'
                },
                'yaxis': {
                    'gridcolor': '#262730',
                    'zerolinecolor': '#262730'
                }
            }
        }
    else:
        return {
            'layout': {
                'paper_bgcolor': '#FFFFFF',
                'plot_bgcolor': '#FFFFFF',
                'font': {'color': '#262730'},
                'xaxis': {
                    'gridcolor': '#E0E0E0',
                    'zerolinecolor': '#E0E0E0'
                },
                'yaxis': {
                    'gridcolor': '#E0E0E0',
                    'zerolinecolor': '#E0E0E0'
                }
            }
        }

def get_chart_colors():
    """Get chart colors based on current theme"""
    theme = get_theme()
    
    if theme == "dark":
        return {
            'primary': '#800020',
            'secondary': '#FFD700',
            'accent': '#4169E1',
            'success': '#28A745',
            'warning': '#FFC107',
            'danger': '#DC3545',
            'text': '#FAFAFA',
            'background': '#0E1117'
        }
    else:
        return {
            'primary': '#800020',
            'secondary': '#FFD700',
            'accent': '#4169E1',
            'success': '#28A745',
            'warning': '#FFC107',
            'danger': '#DC3545',
            'text': '#262730',
            'background': '#FFFFFF'
        }

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
