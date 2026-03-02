import os
import streamlit as st
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
from typing import Optional, Dict, Any

from FraudShield.utils.supabase_client import supabase
from FraudShield.utils.token_manager import AuthTokenManager

import json
import requests
from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests
from pathlib import Path

GOOGLE_SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/userinfo.email",
]

def _load_google_client():
    # Try Streamlit secrets first (best for cloud)
    try:
        secret_json = st.secrets.get("GOOGLE_CLIENT_SECRET_JSON")
        if secret_json:
            return json.loads(secret_json)["web"]
    except Exception:
        pass

    # Fallback to local file (best for local dev)
    with open("client_secret.json", "r", encoding="utf-8") as f:
        return json.load(f)["web"]
        

def _token_mgr() -> AuthTokenManager:
    token_key = os.getenv("TOKEN_KEY")
    if not token_key:
        try:
            token_key = st.secrets.get("TOKEN_KEY")
        except Exception:
            token_key = None

    if not token_key:
        raise RuntimeError("Missing TOKEN_KEY (env/secrets)")

    return AuthTokenManager(
        cookie_name="fraudshield_auth",
        token_key=token_key,
        token_duration_days=7
    )


def profile_exists(email: str) -> bool:
    """Check if a profile exists for the given email."""
    res = supabase.table("profiles").select("email").eq("email", email).limit(1).execute()
    return bool(res.data)


def create_profile(
    email: str,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None
):
    """Create a new profile in the database."""
    payload = {"email": email, "first_name": first_name, "last_name": last_name}
    return supabase.table("profiles").insert(payload).execute()


def get_profile_names(email: str) -> dict:
    """Return {'first_name':..., 'last_name':...} from profiles table."""
    try:
        res = (
            supabase.table("profiles")
            .select("first_name,last_name")
            .eq("email", email)
            .limit(1)
            .execute()
        )
        if res and getattr(res, "data", None):
            return res.data[0] if len(res.data) else {}
    except Exception:
        pass
    return {}


def set_display_name_in_session(first_name: str, last_name: str):
    """Set user display name in session state."""
    first_name = (first_name or "").strip()
    last_name = (last_name or "").strip()

    user_name = f"{first_name} {last_name}".strip() or "user_1"

    if first_name and last_name:
        initials = f"{first_name[0].upper()}{last_name[0].upper()}"
    elif first_name:
        initials = first_name[0].upper()
    elif last_name:
        initials = last_name[0].upper()
    else:
        initials = "U1"

    st.session_state["user_name"] = user_name
    st.session_state["user_initials"] = initials


def login_with_email(email: str, password: str):
    """Login with email and password."""
    # Always returns: (res, err)
    try:
        if not profile_exists(email):
            return None, "Account not found. Please register first."
    except Exception as e:
        return None, f"Profile check failed: {e}"

    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})

        if res and getattr(res, "session", None) and getattr(res, "user", None):
            _token_mgr().set_token(
                email=res.user.email,
                access_token=res.session.access_token,
                refresh_token=res.session.refresh_token,
                provider="app",
            )
            
            # Load profile names into session
            prof = get_profile_names(res.user.email)
            set_display_name_in_session(prof.get("first_name", ""), prof.get("last_name", ""))
            
            return res, None

        return None, "Login failed: no session/user returned."
    except Exception as e:
        return None, str(e)


def register_with_email(email: str, password: str, first_name: str, last_name: str):
    """Register a new user with email and password."""
    if profile_exists(email):
        st.error("❌ This email is already registered. Please login.")
        return None

    try:
        res = supabase.auth.sign_up(
            {
                "email": email,
                "password": password,
                "options": {"data": {"first_name": first_name, "last_name": last_name}},
            }
        )

        # Create profile row immediately
        create_profile(email=email, first_name=first_name, last_name=last_name)

        return res
    except Exception as e:
        st.error(f"❌ Registration failed: {e}")
        return None


def _google_flow():
    """Create Google OAuth flow object."""
    cfg = _load_google_client()

    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")
    if not redirect_uri:
        try:
            redirect_uri = st.secrets.get("GOOGLE_REDIRECT_URI")
        except Exception:
            redirect_uri = "http://localhost:8501"

    redirect_uri = redirect_uri.strip()

    flow = google_auth_oauthlib.flow.Flow.from_client_config(
        {"web": cfg},
        scopes=GOOGLE_SCOPES,
        redirect_uri=redirect_uri,
    )
    return flow


def google_auth_link(label: str, mode: str):
    """
    mode: 'login' or 'register'
    Creates a button that redirects to Google OAuth.
    """
    flow = _google_flow()
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        state=mode,
        prompt="select_account",
    )

    if st.button(label, use_container_width=True):
        st.markdown(
            f"<meta http-equiv='refresh' content='0; url={auth_url}'>",
            unsafe_allow_html=True,
        )
        st.stop()


def handle_google_callback():
    """Handle the Google OAuth callback and exchange code for tokens."""
    qp = dict(st.query_params)
    if "code" not in qp:
        return None

    # Store debug info
    st.session_state["_last_google_qp"] = qp

    code = qp["code"]
    mode = qp.get("state") or "login"

    # Immediately clear query parameters to prevent reuse
    st.query_params.clear()

    cfg = _load_google_client()
    client_id = cfg["client_id"]
    client_secret = cfg["client_secret"]
    
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")
    if not redirect_uri:
        try:
            redirect_uri = st.secrets.get("GOOGLE_REDIRECT_URI")
        except Exception:
            redirect_uri = "http://localhost:8501"

    redirect_uri = redirect_uri.strip()

    token_res = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        },
        timeout=20,
    )

    if token_res.status_code != 200:
        st.session_state.google_error = f"Token exchange failed: {token_res.status_code} - {token_res.text}"
        return None

    token_json = token_res.json()
    id_token = token_json.get("id_token")
    if not id_token:
        st.session_state.google_error = "No id_token returned by Google token exchange."
        return None

    try:
        info = google_id_token.verify_oauth2_token(
            id_token, google_requests.Request(), client_id
        )
    except Exception as e:
        st.session_state.google_error = f"ID token verification failed: {e}"
        return None

    email = info.get("email")
    if not email:
        st.session_state.google_error = "No email in verified token."
        return None

    return {"mode": mode, "email": email, "id_token": id_token}


def google_login_or_register():
    """Complete Google OAuth flow and sign in/register with Supabase."""
    # Clear any previous error
    st.session_state.pop("google_error", None)

    # If already authenticated, don't process
    if st.session_state.get("is_authenticated"):
        return None

    payload = handle_google_callback()
    if payload is None:
        return None

    email = payload["email"]
    id_token = payload["id_token"]

    try:
        res = supabase.auth.sign_in_with_id_token({"provider": "google", "token": id_token})
    except Exception as e:
        st.session_state.google_error = f"Supabase Google sign-in failed: {e}"
        return None

    if not (res and res.session and res.user):
        st.session_state.google_error = "Supabase sign-in returned no user or session."
        return None

    # Make the client adopt the session
    supabase.auth.set_session(res.session.access_token, res.session.refresh_token)

    # Persist tokens in cookie
    _token_mgr().set_token(
        email=res.user.email,
        access_token=res.session.access_token,
        refresh_token=res.session.refresh_token,
        provider="google",
    )

    # Load profile names into session
    prof = get_profile_names(res.user.email)
    set_display_name_in_session(prof.get("first_name", ""), prof.get("last_name", ""))

    # Write local session file for debugging (only in development)
    if not os.getenv("STREAMLIT_SERVER_HEADLESS"):  # Not set on cloud
        try:
            Path(".local_session.json").write_text(
                json.dumps({
                    "access_token": res.session.access_token,
                    "refresh_token": res.session.refresh_token,
                    "email": res.user.email,
                }, indent=2),
                encoding="utf-8",
            )
        except Exception:
            pass

    # Ensure profile exists
    try:
        if not profile_exists(res.user.email):
            create_profile(email=res.user.email)
    except Exception as e:
        st.warning(f"⚠️ Profile creation/check failed: {e}")

    return res.user


def restore_supabase_session_from_cookie() -> bool:
    """
    Restores supabase session using tokens stored in the AuthTokenManager cookie.
    Call this early in your Streamlit app (before you check auth state).
    """
    try:
        decoded = _token_mgr().get_decoded_token()
        if not decoded:
            return False

        access_token = decoded.get("access_token")
        refresh_token = decoded.get("refresh_token")
        if not access_token or not refresh_token:
            return False

        # Adopt the session for Supabase client
        supabase.auth.set_session(access_token, refresh_token)
        
        # Verify the session works
        user_res = supabase.auth.get_user()
        if user_res and user_res.user:
            # Load profile names into session
            prof = get_profile_names(user_res.user.email)
            set_display_name_in_session(prof.get("first_name", ""), prof.get("last_name", ""))
            return True
        return False
    except Exception:
        return False


def logout():
    """Logout user and clear all session data."""
    try:
        supabase.auth.sign_out()
    except Exception:
        pass
    
    _token_mgr().delete_token()
    
    # Clean up local session file if it exists
    try:
        Path(".local_session.json").unlink(missing_ok=True)
    except Exception:
        pass
    
    st.session_state.clear()
    st.rerun()