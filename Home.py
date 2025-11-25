import streamlit as st
from core.auth import login_widget, check_authentication
from core.theme import apply_theme
from pathlib import Path

# Apply consistent branding/theme
apply_theme()

# Load logo path
logo_path = Path(__file__).parent / "assets" / "mind_logo.png"

# Sidebar Branding
with st.sidebar:
    st.image(logo_path, use_column_width=True)
    st.markdown("### **MIND Unified Dashboard**")
    st.markdown("---")

# Authentication Gate
auth_status, user_role, username = check_authentication()

if not auth_status:
    login_widget()
    st.stop()

# Main UI after login
st.title("Welcome to the MIND Unified Dashboard")
st.write(f"Hello **{username}** 👋")
st.write(f"Your role: **{user_role}**")

st.markdown("""
This platform provides real-time analytics and insights across:
- Student Performance  
- Faculty Cohort Insights  
- System Reliability & Environment Quality  
- Institution-wide Administrative KPIs  

Please use the sidebar to navigate the dashboards available to your role.
""")

# Role-based page access reminder
if user_role == "Student":
    st.info("You have access to the **Student Dashboard** only.")
elif user_role == "Faculty":
    st.info("You have access to the **Faculty Dashboard** only.")
elif user_role == "Developer":
    st.info("You have access to the **Developer Dashboard** only.")
elif user_role == "Admin":
    st.success("You have access to **all dashboards**.")

