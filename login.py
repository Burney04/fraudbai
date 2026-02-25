import streamlit as st
import re
from FraudShield.utils.auth import login_with_email, google_auth_link, google_login_or_register
from FraudShield.utils.supabase_client import supabase

def show():
    # temp debug
    st.write("DEBUG query params:", dict(st.query_params))
    st.write("DEBUG last google qp:", st.session_state.get("_last_google_qp"))
    st.write("DEBUG auth:", st.session_state.is_authenticated)
    st.write("DEBUG user:", getattr(st.session_state.get("user"), "email", None))

    def is_valid_email(email: str) -> bool:
        return re.match(r"[^@]+@[^@]+\.[^@]+", email)

    # CSS
    st.markdown("""
    <style>
        [data-testid="stSidebar"], [data-testid="stHeader"] {visibility: hidden;}
        [data-testid="stAppViewContainer"] {
            background: linear-gradient(135deg, #7B2FF7, #F107A3);
            background-attachment: fixed;
            color: black;
        }
        .stForm {
            background: #ffffff;
            padding: 2rem;
            border-radius: 15px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
            color: black;
        }
        h2, p, label, div { color: black !important; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align:center; margin-top:20px;">
        <h2>🔐 Login to FraudbAI</h2>
        <p>Welcome back</p>
    </div>
    """, unsafe_allow_html=True)

    # Email login
    with st.form("login_form"):
        email = st.text_input("Email Address", placeholder="Enter your email")
        password = st.text_input("Password", placeholder="Enter your password", type="password")
        login_button = st.form_submit_button("Login", use_container_width=True)

        if login_button:
            if not email or not password:
                st.error("❌ Please fill in all fields.")
            elif not is_valid_email(email):
                st.error("❌ Invalid email format.")
            else:
                res, err = login_with_email(email, password)

                if res and res.user:
                    st.success("✅ Login successful!")
                    st.session_state.is_authenticated = True
                    st.session_state.user = res.user
                    st.session_state.page = "dashboard"
                    st.rerun()
                else:
                    st.error(f"❌ Login failed: {err or 'Invalid email or password'}")


    st.divider()

    # Google login link (mode=login enforces your “must exist” rule)
    google_auth_link("🔐 Sign in with Google", mode="login")

    # Register redirect
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Don't have an account? Register here", use_container_width=True):
            st.session_state.page = "register"
            st.rerun()