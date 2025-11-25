import streamlit as st
from typing import Tuple


def get_stored_users():
    """
    Reads users and roles from Streamlit Secrets.
    
    Expected secrets.toml format in Streamlit Cloud:

    [users]
    admin = "password123"
    faculty1 = "pass1"
    student1 = "pass2"

    [roles]
    admin = "Admin"
    faculty1 = "Faculty"
    student1 = "Student"
    developer1 = "Developer"
    """

    try:
        users = st.secrets["users"]
        roles = st.secrets["roles"]
        return users, roles
    except Exception:
        st.error("❌ Missing users/roles in Streamlit Secrets.")
        return {}, {}


def login_widget():
    """Shows the login UI."""
    st.title("🔐 Login to MIND Unified Dashboard")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        authenticate(username, password)


def authenticate(username: str, password: str):
    """Validates credentials and sets session state."""

    users, roles = get_stored_users()

    if username in users and users[username] == password:
        st.session_state["authenticated"] = True
        st.session_state["username"] = username
        st.session_state["role"] = roles.get(username, "Student")

        st.success("Login successful ✔")
        st.experimental_rerun()
    else:
        st.error("Invalid username or password")


def check_authentication() -> Tuple[bool, str, str]:
    """
    Returns:
        - is_authenticated (bool)
        - role (str)
        - username (str)
    """

    is_auth = st.session_state.get("authenticated", False)
    role = st.session_state.get("role", None)
    username = st.session_state.get("username", None)

    return is_auth, role, username


def logout_button():
    """Adds a logout button to the sidebar."""
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.experimental_rerun()


def role_guard(required_role: str):
    """
    Ensures the logged-in user has the correct role for this page.
    Admin has access to all pages.
    """

    is_auth, user_role, username = check_authentication()

    if not is_auth:
        st.error("You must log in to access this page.")
        st.stop()

    if user_role != required_role and user_role != "Admin":
        st.error("⛔ Access Denied — You do not have permission to view this page.")
        st.stop()

    return user_role, username

