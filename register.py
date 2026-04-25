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
        /* Style for form buttons - keep consistent width */
        .stForm button {
            width: 100% !important;
        }
        /* Fix for text input fields */
        .stTextInput input {
            text-align: left !important;
            padding-right: 2.5rem !important;
        }
        /* Ensure the password toggle button stays on the right and centered vertically */
        .stTextInput button {
            position: absolute !important;
            right: 0 !important;
            top: 55% !important;
            transform: translateY(-50%) !important;
            width: auto !important;
            min-width: unset !important;
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            padding: 0 10px !important;
            margin-top: 2px !important;
        }
        /* Adjust the container height if needed */
        .stTextInput > div {
            position: relative !important;
        }
        /* White text for form submit button (Register) */
        button[kind="formSubmit"] {
            color: white !important;
        }
        /* Hover effect for form submit button - text turns black */
        button[kind="formSubmit"]:hover {
            color: black !important;
        }
        /* Dark text for regular buttons (Login here) */
        button[kind="secondary"] {
            color: black !important;
        }
        /* White text for link buttons (Google) */
        a button {
            color: white !important;
        }
        /* Hover effect for link buttons - text turns black */
        a button:hover {
            color: black !important;
        }
        /* Fallback for Google button width */
        .stLinkButton > button {
            width: 100% !important;
        }
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

    # Center the Google register button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        google_auth_link("🧾 Register with Google", mode="register")

    # Center the login button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Already have an account? Login here", use_container_width=True):
            st.session_state.page = "login"
            st.rerun()