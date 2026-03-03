import streamlit as st
import re
from FraudShield.utils.auth import login_with_email, google_auth_link, send_password_reset

def show():
    # Initialize session state
    if "show_forgot_password" not in st.session_state:
        st.session_state.show_forgot_password = False

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
        .forgot-link {
            text-align: left;
            margin-top: 5px;
            margin-bottom: 15px;
        }
        .back-to-login {
            text-align: center;
            margin-top: 20px;
        }
        .success-message {
            background-color: #d4edda;
            color: #155724;
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
            text-align: center;
        }
    </style>
    """, unsafe_allow_html=True)

    # Title
    if st.session_state.show_forgot_password:
        st.markdown("""
        <div style="text-align:center; margin-top:20px;">
            <h2>🔐 Reset Password</h2>
            <p>Enter your email to receive a reset link</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="text-align:center; margin-top:20px;">
            <h2>🔐 Login to FraudbAI</h2>
            <p>Welcome back</p>
        </div>
        """, unsafe_allow_html=True)

    # Forgot Password Mode
    if st.session_state.show_forgot_password:
        with st.form("forgot_form"):
            email = st.text_input("Email Address", placeholder="Enter your email")
            
            col1, col2 = st.columns(2)
            with col1:
                sent = st.form_submit_button("Send Reset Link", use_container_width=True)
            with col2:
                back = st.form_submit_button("Back to Login", use_container_width=True)
            
            if sent:
                if not email:
                    st.error("❌ Please enter your email.")
                elif not is_valid_email(email):
                    st.error("❌ Invalid email format.")
                else:
                    with st.spinner("Sending reset link..."):
                        success, message = send_password_reset(email)
                    
                    if success:
                        st.markdown(f'<div class="success-message">{message}</div>', unsafe_allow_html=True)
                        st.info("📧 The link will expire in 1 hour. Check your spam folder if you don't see it.")
                        
                        # Return to Login button
                        return_to_login = st.form_submit_button("Return to Login", use_container_width=True)
                        if return_to_login:
                            st.session_state.show_forgot_password = False
                            st.rerun()
                    else:
                        st.error(message)
            
            if back:
                st.session_state.show_forgot_password = False
                st.rerun()
    
    # Login Mode
    else:
        with st.form("login_form"):
            email = st.text_input("Email Address", placeholder="Enter your email")
            password = st.text_input("Password", placeholder="Enter your password", type="password")
            
            # Create columns with the forgot button on the left
            col_left, col_right = st.columns([1, 1])
            
            with col_left:
                # Forgot password button on the left
                forgot = st.form_submit_button("Forgot password?", use_container_width=True)
            
            with col_right:
                # Empty space or could add something else here
                pass
            
            login_button = st.form_submit_button("Login", use_container_width=True)

            if forgot:
                st.session_state.show_forgot_password = True
                st.rerun()

            if login_button:
                if not email or not password:
                    st.error("❌ Please fill in all fields.")
                elif not is_valid_email(email):
                    st.error("❌ Invalid email format.")
                else:
                    with st.spinner("Logging in..."):
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
        google_auth_link("🔐 Sign in with Google", mode="login")

        if st.button("Don't have an account? Register here", use_container_width=True):
            st.session_state.page = "register"
            st.rerun()