import os
import streamlit as st

# Load .env for local development (optional)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def get_env_or_secret(key):
    """Get from environment variable or st.secrets safely."""
    # First try environment variable
    value = os.getenv(key)
    if value is not None:
        return value
    # Then try st.secrets, but only if accessible without error
    try:
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        # secrets not available, ignore
        pass
    return None

# Populate environment variables from either source
for k in ["SUPABASE_URL", "SUPABASE_KEY", "TOKEN_KEY", "GOOGLE_REDIRECT_URI"]:
    v = get_env_or_secret(k)
    if v:
        os.environ[k] = v

# Set default for GOOGLE_REDIRECT_URI if still missing
if "GOOGLE_REDIRECT_URI" not in os.environ:
    os.environ["GOOGLE_REDIRECT_URI"] = "http://localhost:8501"

# Handle GOOGLE_CLIENT_SECRET_JSON (for cloud secrets)
client_secret_json = get_env_or_secret("GOOGLE_CLIENT_SECRET_JSON")
if client_secret_json and not os.path.exists("client_secret.json"):
    with open("client_secret.json", "w", encoding="utf-8") as f:
        f.write(client_secret_json)

# Now import your modules
import login
import register
from FraudShield import dashboard
from FraudShield.utils.session import init_session_state, restore_session_from_cookie
from FraudShield.utils.auth import google_login_or_register

# Initialize session
init_session_state()

# Handle Google OAuth callback BEFORE any page rendering
if "code" in st.query_params:
    try:
        user = google_login_or_register()
        if user:
            st.session_state.is_authenticated = True
            st.session_state.user = user
            st.session_state.page = "dashboard"
            st.query_params.clear()
            st.rerun()
        else:
            st.error("Google Auth failed to return a user session.")
            st.stop()
    except Exception as e:
        st.error(f"Critical Auth Error: {e}")
        st.stop()

# Restore existing session if not authenticated
if not st.session_state.is_authenticated:
    restore_session_from_cookie()

# Routing
if st.session_state.is_authenticated:
    st.session_state.page = "dashboard"
elif "page" not in st.session_state:
    st.session_state.page = "login"

if st.session_state.page == "login":
    login.show()
elif st.session_state.page == "register":
    register.show()
elif st.session_state.page == "dashboard":
    dashboard.show()