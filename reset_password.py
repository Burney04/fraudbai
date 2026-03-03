import streamlit as st
from FraudShield.utils.supabase_client import supabase

def show():
    st.set_page_config(page_title="Reset Password", page_icon="🔐")
    
    # Hide sidebar
    st.markdown("""
    <style>
        [data-testid="stSidebar"] {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style="text-align:center; margin-top:20px;">
        <h2>🔐 Reset Your Password</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Check if we have tokens in the URL hash (via JavaScript)
    query_params = st.query_params
    access_token = query_params.get("access_token")
    refresh_token = query_params.get("refresh_token")
    type_param = query_params.get("type")
    
    # If we don't have tokens yet, use JavaScript to extract them
    if not access_token:
        st.markdown("""
        <script>
        // Extract tokens from URL hash
        const hash = window.location.hash.substring(1);
        if (hash) {
            // Parse hash parameters
            const params = new URLSearchParams(hash);
            const accessToken = params.get('access_token');
            const refreshToken = params.get('refresh_token');
            const type = params.get('type');
            
            if (accessToken && type === 'recovery') {
                // Redirect with query parameters
                window.location.href = window.location.pathname + 
                    '?access_token=' + encodeURIComponent(accessToken) +
                    '&refresh_token=' + encodeURIComponent(refreshToken || '') +
                    '&type=' + encodeURIComponent(type);
            }
        }
        </script>
        """, unsafe_allow_html=True)
        
        st.info("Processing your reset link...")
        return
    
    # We have tokens, show password reset form
    if type_param == "recovery":
        # Set the session with recovery tokens
        supabase.auth.set_session(access_token, refresh_token or "")
        
        st.markdown("""
        <div style="background: white; padding: 2rem; border-radius: 10px; margin-top: 20px;">
            <h3>Enter New Password</h3>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("new_password_form"):
            new_password = st.text_input("New Password", type="password", placeholder="Enter new password")
            confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm new password")
            
            col1, col2 = st.columns(2)
            with col1:
                submit = st.form_submit_button("Update Password", use_container_width=True)
            with col2:
                if st.form_submit_button("Back to Login", use_container_width=True):
                    st.session_state.page = "login"
                    st.rerun()
            
            if submit:
                if not new_password or not confirm_password:
                    st.error("❌ Please fill in all fields.")
                elif len(new_password) < 8:
                    st.error("❌ Password must be at least 8 characters.")
                elif new_password != confirm_password:
                    st.error("❌ Passwords do not match.")
                else:
                    try:
                        supabase.auth.update_user({"password": new_password})
                        st.success("✅ Password updated successfully!")
                        st.balloons()
                        st.info("Redirecting to login...")
                        st.session_state.page = "login"
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Failed to update password: {e}")
    else:
        st.error("Invalid reset link.")
        if st.button("Back to Login"):
            st.session_state.page = "login"
            st.rerun()