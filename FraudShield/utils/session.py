import os
import streamlit as st
from FraudShield.utils.supabase_client import supabase
from FraudShield.utils.token_manager import AuthTokenManager
from pathlib import Path
import json

def init_session_state():
    if "is_authenticated" not in st.session_state:
        st.session_state.is_authenticated = False
    if "user" not in st.session_state:
        st.session_state.user = None
    if "page" not in st.session_state:
        st.session_state.page = "login"


def restore_session_from_cookie():
    token_key = os.getenv("TOKEN_KEY")
    if not token_key:
        try:
            token_key = st.secrets.get("TOKEN_KEY")
        except Exception:
            token_key = None
    if not token_key:
        return False

    def _apply_session(access_token: str, refresh_token: str) -> bool:
        if not access_token or not refresh_token:
            return False
        supabase.auth.set_session(access_token=access_token, refresh_token=refresh_token)
        user_res = supabase.auth.get_user()
        if user_res and user_res.user:
            st.session_state.is_authenticated = True
            st.session_state.user = user_res.user
            return True
        return False

    # 1) Try cookie (normal path)
    try:
        mgr = AuthTokenManager(cookie_name="fraudshield_auth", token_key=token_key, token_duration_days=7)
        data = mgr.get_decoded_token()
        if data and _apply_session(data.get("access_token"), data.get("refresh_token")):
            # st.write("DEBUG restored from cookie")
            return True
    except Exception:
        pass

    # 2) DEV fallback: restore from local file (your auth.py writes this)
    if not os.getenv("STREAMLIT_SERVER_HEADLESS"):
        try:
            p = Path(".local_session.json")
            if p.exists():
                data2 = json.loads(p.read_text(encoding="utf-8"))
                if _apply_session(data2.get("access_token"), data2.get("refresh_token")):
                    return True
        except Exception:
            pass

    return False


def clear_session():
    st.session_state.is_authenticated = False
    st.session_state.user = None
    try:
        Path(".local_session.json").unlink(missing_ok=True)
    except Exception:
        pass