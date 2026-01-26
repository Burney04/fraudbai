import os
import streamlit as st

for k in ["SUPABASE_URL", "SUPABASE_KEY", "TOKEN_KEY", "GOOGLE_REDIRECT_URI"]:
    if k in st.secrets:
        os.environ[k] = str(st.secrets[k])

if "GOOGLE_CLIENT_SECRET_JSON" in st.secrets and not os.path.exists("client_secret.json"):
    with open("client_secret.json", "w", encoding="utf-8") as f:
        f.write(str(st.secrets["GOOGLE_CLIENT_SECRET_JSON"]))

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