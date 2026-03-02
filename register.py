import streamlit as st
import re
from FraudShield.utils.auth import register_with_email, google_auth_link, google_login_or_register
from FraudShield.utils.supabase_client import supabase

def show():
    def is_valid_email(email: str) -> bool:
        return re.match(r"[^@]+@[^@]+\.[^@]+", email)

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
        <h2>📝 Register for FraudbAI</h2>
        <p>Enter your credentials below to continue</p>
    </div>
    """, unsafe_allow_html=True)

    with st.form("register_form"):
        col1, col2 = st.columns(2)
        with col1:
            first_name = st.text_input("First Name", placeholder="Enter your first name")
        with col2:
            last_name = st.text_input("Last Name", placeholder="Enter your last name")

        email = st.text_input("Email Address", placeholder="Enter your email address")
        password = st.text_input("Password", placeholder="Enter a strong password", type="password")
        confirm = st.text_input("Confirm Password", placeholder="Re-enter your password", type="password")

        register_button = st.form_submit_button("Register", use_container_width=True)

        if register_button:
            if not first_name or not last_name or not email or not password or not confirm:
                st.error("❌ Please fill in all fields.")
            elif not is_valid_email(email):
                st.error("❌ Invalid email format.")
            elif len(password) < 8:
                st.error("❌ Password must be at least 8 characters long.")
            elif password != confirm:
                st.error("❌ Passwords do not match.")
            else:
                res = register_with_email(email, password, first_name, last_name)
                if res and res.user:
                    st.success("✅ Registration successful! Please log in.")
                    st.session_state.page = "login"
                    st.rerun()

    st.divider()

    # Google register (mode=register creates profile if missing)
    google_auth_link("🧾 Register with Google", mode="register")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Already have an account? Login here", use_container_width=True):
            st.session_state.page = "login"
            st.rerun()