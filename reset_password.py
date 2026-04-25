import streamlit as st
from FraudShield.utils.supabase_client import supabase

def show():
    st.set_page_config(page_title="Reset Password", page_icon="🔐")
    
    # Hide sidebar
    st.markdown("""
    <style>
        [data-testid="stSidebar"] {visibility: hidden;}
        [data-testid="stAppViewContainer"] {
            background: linear-gradient(135deg, #7B2FF7, #F107A3);
            background-attachment: fixed;
        }
        .reset-container {
            background: white;
            padding: 2rem;
            border-radius: 15px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
            margin-top: 20px;
        }
        .stButton button {
            width: 100% !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style="text-align:center; margin-top:20px;">
        <h2>🔐 Reset Your Password</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Get query parameters - looking for token_hash instead of access_token
    query_params = st.query_params
    token_hash = query_params.get("token_hash")
    type_param = query_params.get("type")
    
    # Check for legacy fragment-based tokens (for backward compatibility)
    access_token = query_params.get("access_token")
    refresh_token = query_params.get("refresh_token")
    
    # Container for the main content
    with st.container():
        st.markdown('<div class="reset-container">', unsafe_allow_html=True)
        
        # Handle legacy fragment-based links (if user clicks old email link)
        if not token_hash and not access_token:
            st.markdown("""
            <script>
            // Extract tokens from URL hash for legacy links
            const hash = window.location.hash.substring(1);
            if (hash) {
                const params = new URLSearchParams(hash);
                const accessToken = params.get('access_token');
                const refreshToken = params.get('refresh_token');
                const type = params.get('type');
                
                if (accessToken && type === 'recovery') {
                    window.location.href = window.location.pathname + 
                        '?access_token=' + encodeURIComponent(accessToken) +
                        '&refresh_token=' + encodeURIComponent(refreshToken || '') +
                        '&type=' + encodeURIComponent(type);
                }
            }
            </script>
            """, unsafe_allow_html=True)
            
            st.warning("⚠️ Invalid or missing reset token. Please request a new password reset link.")
            if st.button("← Back to Login", use_container_width=True):
                st.session_state.page = "login"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
            return
        
        # Handle legacy access_token flow (for backward compatibility)
        if access_token and not token_hash:
            if type_param == "recovery":
                try:
                    # Legacy method - set session with tokens
                    supabase.auth.set_session(access_token, refresh_token or "")
                    st.success("✅ Token verified. You can now set a new password.")
                    show_password_form = True
                except Exception as e:
                    st.error(f"❌ Invalid or expired reset link. Please request a new one.")
                    if st.button("← Back to Login", use_container_width=True):
                        st.session_state.page = "login"
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
                    return
            else:
                st.error("❌ Invalid reset link type.")
                if st.button("← Back to Login", use_container_width=True):
                    st.session_state.page = "login"
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
                return
        # Handle new token_hash flow (recommended for Streamlit Cloud)
        elif token_hash and type_param == "recovery":
            try:
                # Verify the OTP token - this is more reliable on Streamlit Cloud
                supabase.auth.verify_otp({
                    "token_hash": token_hash,
                    "type": "recovery"
                })
                st.success("✅ Token verified. You can now set a new password.")
                show_password_form = True
            except Exception as e:
                st.error(f"❌ Password reset link is invalid or has expired. Please request a new one.")
                if st.button("← Back to Login", use_container_width=True):
                    st.session_state.page = "login"
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
                return
        else:
            st.error("❌ Invalid reset link.")
            if st.button("← Back to Login", use_container_width=True):
                st.session_state.page = "login"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
            return
        
        # Show password reset form if token verification succeeded
        if show_password_form:
            st.markdown("### Enter New Password")
            st.markdown("Please create a strong password for your account.")
            
            with st.form("new_password_form"):
                new_password = st.text_input(
                    "New Password", 
                    type="password", 
                    placeholder="Enter new password",
                    help="Password must be at least 8 characters"
                )
                confirm_password = st.text_input(
                    "Confirm Password", 
                    type="password", 
                    placeholder="Confirm new password"
                )
                
                col1, col2 = st.columns(2)
                with col1:
                    submit = st.form_submit_button("🔐 Update Password", use_container_width=True)
                with col2:
                    cancel = st.form_submit_button("← Cancel", use_container_width=True)
                
                if cancel:
                    # Sign out if we had a session
                    try:
                        supabase.auth.sign_out()
                    except:
                        pass
                    st.session_state.page = "login"
                    st.rerun()
                
                if submit:
                    if not new_password or not confirm_password:
                        st.error("❌ Please fill in all fields.")
                    elif len(new_password) < 8:
                        st.error("❌ Password must be at least 8 characters long.")
                    elif new_password != confirm_password:
                        st.error("❌ Passwords do not match.")
                    elif not any(c.isupper() for c in new_password):
                        st.error("❌ Password must contain at least one uppercase letter.")
                    elif not any(c.islower() for c in new_password):
                        st.error("❌ Password must contain at least one lowercase letter.")
                    elif not any(c.isdigit() for c in new_password):
                        st.error("❌ Password must contain at least one number.")
                    else:
                        try:
                            with st.spinner("Updating your password..."):
                                # Update the user's password
                                supabase.auth.update_user({"password": new_password})
                                
                                # Sign out the user for security
                                try:
                                    supabase.auth.sign_out()
                                except:
                                    pass
                                
                                st.success("✅ Password updated successfully!")
                                st.balloons()
                                st.info("🔐 Your password has been reset. Please log in with your new password.")
                                
                                # Add a small delay before redirecting
                                import time
                                time.sleep(2)
                                
                                # Redirect to login
                                st.session_state.page = "login"
                                st.rerun()
                                
                        except Exception as e:
                            error_msg = str(e)
                            if "same as old password" in error_msg.lower():
                                st.error("❌ New password must be different from your old password.")
                            else:
                                st.error(f"❌ Failed to update password: {error_msg}")
        
        st.markdown('</div>', unsafe_allow_html=True)

# For backwards compatibility with direct script execution
if __name__ == "__main__":
    show()