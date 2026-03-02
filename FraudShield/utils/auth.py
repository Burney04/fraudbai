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
    # Assumes you have a public.profiles table with an email column
    res = supabase.table("profiles").select("email").eq("email", email).limit(1).execute()
    return bool(res.data)


def create_profile(
    email: str,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None
):
    payload = {"email": email, "first_name": first_name, "last_name": last_name}
    return supabase.table("profiles").insert(payload).execute()


def login_with_email(email: str, password: str):
    if not profile_exists(email):
        return None, "Account not found. Please register first."

    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if res and res.session and res.user:
            _token_mgr().set_token(
                email=res.user.email,
                access_token=res.session.access_token,
                refresh_token=res.session.refresh_token,
                provider="app",
            )
        return res, None
    except Exception as e:
        # Show the real error during debugging
        return None, str(e)


def register_with_email(email: str, password: str, first_name: str, last_name: str):
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

        # Create profile row immediately (works even if email confirmation is enabled)
        create_profile(email=email, first_name=first_name, last_name=last_name)

        return res
    except Exception as e:
        st.error(f"❌ Registration failed: {e}")
        return None


def _google_flow():
    cfg = _load_google_client()

    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")
    if not redirect_uri:
        try:
            redirect_uri = st.secrets.get("GOOGLE_REDIRECT_URI")
        except Exception:
            redirect_uri = "http://localhost:8502"

    redirect_uri = redirect_uri.strip()

    # DEBUG (temporary)
    st.write("DEBUG oauth client_id:", cfg.get("client_id"))
    st.write("DEBUG redirect_uri:", redirect_uri)

    flow = google_auth_oauthlib.flow.Flow.from_client_config(
        {"web": cfg},
        scopes=GOOGLE_SCOPES,
        redirect_uri=redirect_uri,
    )
    return flow


# 1. First, define the URL generator
def get_google_auth_url(mode: str = "login"):
    client_config = _load_google_client()
    
    # Ensure this matches your Google Console exactly
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")
    if not redirect_uri:
        try:
            redirect_uri = st.secrets.get("GOOGLE_REDIRECT_URI")
        except:
            redirect_uri = "https://fraudshield-app.streamlit.app" # Hardcode fallback

    flow = google_auth_oauthlib.flow.Flow.from_client_config(
        {"web": client_config},
        scopes=GOOGLE_SCOPES,
        redirect_uri=redirect_uri.strip()
    )
    
    # We remove 'state' temporarily to ensure no mismatch 403s
    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true"
    )
    return authorization_url

def google_auth_link(label: str, mode: str):
    flow = _google_flow()
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        state=mode,
        prompt="select_account",
    )
    st.write("DEBUG auth_url:", auth_url)  # <-- add this line

    st.link_button(label, auth_url, use_container_width=True)

def handle_google_callback():
    qp = dict(st.query_params)
    if "code" not in qp:
        return None

    # keep debug for your UI
    st.session_state["_last_google_qp"] = qp

    code = qp["code"]
    mode = qp.get("state") or "login"

    cfg = _load_google_client()
    client_id = cfg["client_id"]
    client_secret = cfg["client_secret"]

    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")
    if not redirect_uri:
        try:
               redirect_uri = st.secrets.get("GOOGLE_REDIRECT_URI")
        except Exception:
            redirect_uri = "http://localhost:8502"

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
    token_res.raise_for_status()
    token_json = token_res.json()

    idt = token_json.get("id_token")
    if not idt:
        st.error("No id_token returned by Google token exchange.")
        return None

    info = google_id_token.verify_oauth2_token(
        idt, google_requests.Request(), client_id
    )
    email = info.get("email")

    # clear AFTER successful processing
    st.query_params.clear()

    return {"mode": mode, "email": email, "id_token": idt}
    
    
def google_login_or_register():
    try:
        payload = handle_google_callback()
    except Exception as e:
        st.error(f"❌ Google callback failed: {e}")
        return None

    if not payload:
        return None

    email = payload.get("email")
    id_token = payload.get("id_token")

    st.write("DEBUG google email:", email)
    st.write("DEBUG has id_token:", bool(id_token))

    if not email or not id_token:
        st.error("❌ Google auth failed (missing email or id_token).")
        return None

    try:
        res = supabase.auth.sign_in_with_id_token({"provider": "google", "token": id_token})
        st.write("DEBUG supabase sign_in_with_id_token ok:", bool(res and res.user))
    except Exception as e:
        st.error(f"❌ Supabase Google sign-in failed: {e}")
        return None

    if not (res and res.session and res.user):
        st.error("❌ Supabase Google sign-in failed (no session returned).")
        return None

    # Make the client adopt the session (important for future get_user calls)
    supabase.auth.set_session(res.session.access_token, res.session.refresh_token)

    # Persist tokens
    _token_mgr().set_token(
        email=res.user.email,
        access_token=res.session.access_token,
        refresh_token=res.session.refresh_token,
        provider="google",
    )

    from pathlib import Path
    import json
    import os

    # Only write local debug session file when running locally
    if not os.getenv("STREAMLIT_SERVER_HEADLESS"):  # usually set on cloud/server runs
        Path(".local_session.json").write_text(
            json.dumps(
                {
                    "access_token": res.session.access_token,
                    "refresh_token": res.session.refresh_token,
                    "email": res.user.email,
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    # Ensure profile exists (don’t block login if it fails)
    try:
        if not profile_exists(res.user.email):
            create_profile(email=res.user.email)
    except Exception as e:
        st.warning(f"⚠️ Logged in, but profile creation/check failed: {e}")

    return res.user


def logout():
    try:
        supabase.auth.sign_out()
    except Exception:
        pass
    _token_mgr().delete_token()
    st.session_state.clear()
    st.rerun()