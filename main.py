import os
import streamlit as st

# Load .env locally (Streamlit Cloud won't have it; safe if missing)
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


def get_secret(name: str, default=None):
    """
    Priority:
    1) Streamlit secrets (Cloud or local secrets.toml)
    2) Environment variables (.env loaded into env)
    """
    # Try Streamlit secrets safely (won't crash if secrets.toml doesn't exist)
    try:
        if name in st.secrets:
            return str(st.secrets[name])
    except Exception:
        pass

    # Fall back to env
    val = os.getenv(name)
    return val if val is not None else default


# Populate environment variables used by the rest of your app
for k in ["SUPABASE_URL", "SUPABASE_KEY", "TOKEN_KEY", "GOOGLE_REDIRECT_URI"]:
    v = get_secret(k)
    if v:
        os.environ[k] = v


# Handle GOOGLE_CLIENT_SECRET_JSON
# - In Streamlit Cloud: store it in Secrets as a TOML multiline string
# - Locally: you can keep it in .env as a JSON string
client_secret_json = get_secret("GOOGLE_CLIENT_SECRET_JSON")

if client_secret_json and not os.path.exists("client_secret.json"):
    with open("client_secret.json", "w", encoding="utf-8") as f:
        f.write(client_secret_json)


import login
import register
from FraudShield import dashboard
from FraudShield.utils.session import init_session_state, restore_session_from_cookie

init_session_state()

# Restore once per run
if not st.session_state.is_authenticated:
    restore_session_from_cookie()

# Route
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