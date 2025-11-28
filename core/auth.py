import streamlit as st
import re
from typing import Tuple, Optional, Dict

# --- Configuration Constants (Aligning with Architecture Overview) ---
# NOTE: For real-world use, replace this simple list check with JWT and bcrypt hashing.
ROLE_CONFIG_KEYS = {
    "Admin": "ADMIN_USERS",
    "Faculty": "FACULTY_USERS",
    "Developer": "DEVELOPER_USERS",
    # Student is default if not found in any other list
}
# Define a placeholder secret for the simple login mechanism
LOGIN_SECRET_KEY = "LOGIN_SECRET"


def get_stored_config() -> Optional[Dict[str, str]]:
    """Reads role configuration from Streamlit Secrets."""
    
    # Check if any role list or the login secret is missing
    missing_secrets = [key for key in ROLE_CONFIG_KEYS.values() if key not in st.secrets]
    if LOGIN_SECRET_KEY not in st.secrets:
        missing_secrets.append(LOGIN_SECRET_KEY)

    if missing_secrets:
        # Using markdown formatting to show the missing keys clearly
        st.error(f"❌ Missing required keys in Streamlit Secrets: {', '.join(missing_secrets)}")
        st.stop()
    
    return st.secrets


@st.cache_data(show_spinner=False)
def get_user_role(username: str) -> str:
    """
    Determines the user's role by checking against the comma-separated lists 
    stored in Streamlit secrets.
    """
    secrets = get_stored_config()
    if not secrets:
        return "Unauthorized"

    # Normalize username (emails are case-insensitive)
    norm_username = username.lower()

    # Check against roles in a defined hierarchy (Admin first)
    for role, key in ROLE_CONFIG_KEYS.items():
        # Get the comma-separated string, default to empty
        user_list_str = secrets.get(key, "")
        
        # Split the string, strip whitespace, and normalize case
        user_list = [u.strip().lower() for u in user_list_str.split(',') if u.strip()]
        
        if norm_username in user_list:
            return role
            
    # If the user is not explicitly listed, they are considered a Student
    return "Student"


def login_widget():
    """Shows the login UI."""
    st.title("🔐 Login to MIND Unified Dashboard")

    username = st.text_input("Username (e.g., admin@example.com)")
    # NOTE: The password here is purely for local testing and MUST be replaced 
    # with a secure JWT flow in a real application.
    password = st.text_input("Password (anything for local role testing)", type="password")

    # Use a specific Streamlit secret as the "dummy" password for all logins.
    # This prevents the app from being accessed without knowing this one secret.
    DUMMY_PASSWORD = st.secrets.get(LOGIN_SECRET_KEY, "your_local_jwt_secret")


    if st.button("Login"):
        # Basic validation: ensure username and a password (even the dummy one) is provided
        if username and password:
            if password == DUMMY_PASSWORD:
                authenticate(username)
            else:
                 st.error("Invalid password")
        else:
             st.error("Please enter both username and password.")


def authenticate(username: str):
    """
    Sets session state if the username is recognized (i.e., has a role).
    """

    user_role = get_user_role(username)

    if user_role != "Unauthorized":
        st.session_state["authenticated"] = True
        st.session_state["username"] = username
        st.session_state["role"] = user_role

        st.success(f"Login successful ✔ Role: **{user_role}**")
        st.rerun()
    else:
        # This branch should only be hit if get_user_role returns "Unauthorized"
        st.error("Invalid username or password")


def check_authentication() -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Returns the current authentication state and user details.

    Returns:
        - is_authenticated (bool)
        - role (str)
        - username (str)
    """

    # Initialize session state keys if they don't exist
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
        st.session_state["role"] = None
        st.session_state["username"] = None


    is_auth = st.session_state["authenticated"]
    role = st.session_state["role"]
    username = st.session_state["username"]

    return is_auth, role, username


def logout_button():
    """Adds a logout button to the sidebar."""
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        # Use st.rerun() to immediately trigger the login page display
        st.rerun()


def role_guard(required_role: str) -> Tuple[str, str]:
    """
    Ensures the logged-in user has the correct role for this page.
    Admin has access to all pages.

    Returns:
        - user_role (str)
        - username (str)
    """

    is_auth, user_role, username = check_authentication()

    # 1. Check if authenticated
    if not is_auth or user_role is None or username is None:
        st.error("You must log in to access this page.")
        # Stop execution of the rest of the Streamlit page script
        st.stop() 

    # 2. Check Role Authorization
    if user_role != required_role and user_role != "Admin":
        st.error(f"⛔ Access Denied — Only **{required_role}** or **Admin** users can view this page. Your role is **{user_role}**.")
        st.stop()

    return user_role, username
