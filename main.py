import os
import streamlit as st

# 1. LOAD ENV VARS FIRST
for k in ["SUPABASE_URL", "SUPABASE_KEY", "TOKEN_KEY", "GOOGLE_REDIRECT_URI"]:
    if k in st.secrets:
        os.environ[k] = str(st.secrets[k])

if "GOOGLE_CLIENT_SECRET_JSON" in st.secrets and not os.path.exists("client_secret.json"):
    with open("client_secret.json", "w", encoding="utf-8") as f:
        f.write(str(st.secrets["GOOGLE_CLIENT_SECRET_JSON"]))

# 2. IMPORTS
import login
import register
from FraudShield import dashboard
from FraudShield.utils.session import init_session_state, restore_session_from_cookie
from FraudShield.utils.auth import google_login_or_register

# 3. INITIALIZE SESSION
init_session_state()

# 4. THE INTERCEPTOR (CRITICAL FIX)
# We check for the Google 'code' BEFORE doing anything else.
# 4. THE INTERCEPTOR (STRENGTHENED)
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
            # THIS PREVENTS THE JSON DUMP BY STOPPING THE SCRIPT
            st.error("Google Auth failed to return a user session.")
            st.stop() 
    except Exception as e:
        st.error(f"Critical Auth Error: {e}")
        st.stop()

# 5. RESTORE EXISTING SESSION
if not st.session_state.is_authenticated:
    restore_session_from_cookie()

# 6. ROUTING LOGIC
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