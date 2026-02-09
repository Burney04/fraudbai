import os
import streamlit as st
from FraudShield.utils.supabase_client import supabase
from FraudShield.utils.token_manager import AuthTokenManager
from FraudShield.utils.auth import get_profile_names, set_display_name_in_session  # Add this import

def init_session_state():
    st.session_state.setdefault("is_authenticated", False)
    st.session_state.setdefault("user", None)
    st.session_state.setdefault("page", "login")
    st.session_state.setdefault("user_name", None)  # Add these
    st.session_state.setdefault("user_initials", None)

def restore_session_from_cookie():
    token_key = os.getenv("TOKEN_KEY")
    if not token_key:
        return False

    mgr = AuthTokenManager(cookie_name="fraudshield_auth", token_key=token_key, token_duration_days=7)
    data = mgr.get_decoded_token()
    if not data:
        return False

    # Restore Supabase session
    try:
        supabase.auth.set_session(
            access_token=data["access_token"],
            refresh_token=data["refresh_token"],
        )
        user_res = supabase.auth.get_user()
        if user_res and user_res.user:
            st.session_state.is_authenticated = True
            st.session_state.user = user_res.user
            
            # Load profile names
            prof = get_profile_names(user_res.user.email)
            set_display_name_in_session(prof.get("first_name", ""), prof.get("last_name", ""))
            
            return True
    except Exception as e:
        st.error(f"Session restoration failed: {e}")
    
    return False

def clear_session():
    st.session_state.is_authenticated = False
    st.session_state.user = None
    st.session_state.user_name = None  # Clear these too
    st.session_state.user_initials = None