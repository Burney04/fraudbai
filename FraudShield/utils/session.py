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

    try:
        # Set the session with the tokens from the cookie
        supabase.auth.set_session(
            access_token=data["access_token"],
            refresh_token=data["refresh_token"],
        )
        user_res = supabase.auth.get_user()
        if user_res and user_res.user:
            # Session is still valid
            st.session_state.is_authenticated = True
            st.session_state.user = user_res.user
            prof = get_profile_names(user_res.user.email)
            set_display_name_in_session(prof.get("first_name", ""), prof.get("last_name", ""))
            return True
        else:
            # get_user returned empty – token probably expired
            raise Exception("get_user returned no user")  # Force refresh attempt
    except Exception as e:
        # Token expired or invalid – try to refresh using the refresh_token
        st.warning(f"Session invalid, attempting refresh: {e}")
        try:
            refresh_res = supabase.auth.refresh_session(data["refresh_token"])
            if refresh_res and refresh_res.session:
                # Refresh succeeded – update cookie and session state
                mgr.set_token(
                    email=refresh_res.user.email,
                    access_token=refresh_res.session.access_token,
                    refresh_token=refresh_res.session.refresh_token,
                    provider=data.get("provider", "app"),
                )
                st.session_state.is_authenticated = True
                st.session_state.user = refresh_res.user
                prof = get_profile_names(refresh_res.user.email)
                set_display_name_in_session(prof.get("first_name", ""), prof.get("last_name", ""))
                return True
            else:
                st.error("Refresh failed: no session returned")
        except Exception as refresh_e:
            st.error(f"Refresh also failed: {refresh_e}")

    # If everything failed, delete the corrupted cookie
    mgr.delete_token()
    return False

def clear_session():
    st.session_state.is_authenticated = False
    st.session_state.user = None
    st.session_state.user_name = None  # Clear these too
    st.session_state.user_initials = None