import os
import streamlit as st
from FraudShield.utils.supabase_client import supabase
from FraudShield.utils.token_manager import AuthTokenManager
from FraudShield.utils.auth import get_profile_names, set_display_name_in_session
from pathlib import Path
import json

def init_session_state():
    """Initialize all session state variables."""
    st.session_state.setdefault("is_authenticated", False)
    st.session_state.setdefault("user", None)
    st.session_state.setdefault("page", "login")
    st.session_state.setdefault("user_name", None)
    st.session_state.setdefault("user_initials", None)

def restore_session_from_cookie():
    """Restore session from cookie or local fallback file."""
    # Get token key from env or secrets
    token_key = os.getenv("TOKEN_KEY")
    if not token_key:
        try:
            token_key = st.secrets.get("TOKEN_KEY")
        except Exception:
            token_key = None
    if not token_key:
        return False

    def _apply_session(access_token: str, refresh_token: str) -> bool:
        """Internal helper to apply a session and update session state."""
        if not access_token or not refresh_token:
            return False
        
        try:
            supabase.auth.set_session(access_token=access_token, refresh_token=refresh_token)
            user_res = supabase.auth.get_user()
            if user_res and user_res.user:
                st.session_state.is_authenticated = True
                st.session_state.user = user_res.user
                
                # Load profile names and set display name
                prof = get_profile_names(user_res.user.email)
                set_display_name_in_session(prof.get("first_name", ""), prof.get("last_name", ""))
                return True
        except Exception:
            pass
        return False

    # 1) Try cookie (normal path)
    try:
        mgr = AuthTokenManager(
            cookie_name="fraudshield_auth", 
            token_key=token_key, 
            token_duration_days=7
        )
        data = mgr.get_decoded_token()
        if data and _apply_session(data.get("access_token"), data.get("refresh_token")):
            return True
    except Exception:
        pass

    # 2) Try refresh if cookie exists but session invalid
    try:
        if data and data.get("refresh_token"):
            refresh_res = supabase.auth.refresh_session(data["refresh_token"])
            if refresh_res and refresh_res.session:
                # Update cookie with new tokens
                mgr.set_token(
                    email=refresh_res.user.email,
                    access_token=refresh_res.session.access_token,
                    refresh_token=refresh_res.session.refresh_token,
                    provider=data.get("provider", "app"),
                )
                # Apply the new session
                return _apply_session(
                    refresh_res.session.access_token, 
                    refresh_res.session.refresh_token
                )
    except Exception:
        pass

    # 3) DEV fallback: restore from local file (for debugging)
    if not os.getenv("STREAMLIT_SERVER_HEADLESS"):  # Not in cloud
        try:
            p = Path(".local_session.json")
            if p.exists():
                data2 = json.loads(p.read_text(encoding="utf-8"))
                if _apply_session(data2.get("access_token"), data2.get("refresh_token")):
                    return True
        except Exception:
            pass

    # If everything failed, try to clean up
    try:
        mgr.delete_token()
    except Exception:
        pass
    
    return False

def clear_session():
    """Clear all session data and clean up files."""
    st.session_state.is_authenticated = False
    st.session_state.user = None
    st.session_state.user_name = None
    st.session_state.user_initials = None
    
    # Clean up local session file if it exists
    try:
        Path(".local_session.json").unlink(missing_ok=True)
    except Exception:
        pass
    
    # Try to delete cookie
    try:
        token_key = os.getenv("TOKEN_KEY")
        if not token_key:
            try:
                token_key = st.secrets.get("TOKEN_KEY")
            except Exception:
                token_key = None
        if token_key:
            mgr = AuthTokenManager(
                cookie_name="fraudshield_auth", 
                token_key=token_key, 
                token_duration_days=7
            )
            mgr.delete_token()
    except Exception:
        pass