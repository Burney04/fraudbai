import os
import streamlit as st
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
from typing import Optional, Dict, Any

from FraudShield.utils.supabase_client import supabase
from FraudShield.utils.token_manager import AuthTokenManager


GOOGLE_SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/userinfo.email",
]


def _token_mgr() -> AuthTokenManager:
    token_key = os.getenv("TOKEN_KEY")
    if not token_key:
        raise RuntimeError("Missing TOKEN_KEY in .env")
    return AuthTokenManager(cookie_name="fraudshield_auth", token_key=token_key, token_duration_days=7)


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
    secret_path = os.getenv("GOOGLE_CLIENT_SECRET_FILE", "client_secret.json")
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8501")

    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        secret_path,
        scopes=GOOGLE_SCOPES,
        redirect_uri=redirect_uri,
    )
    return flow


def google_auth_link(label: str, mode: str):
    """
    mode: 'login' or 'register'
    Redirects in the SAME tab to avoid Streamlit session reset.
    """
    flow = _google_flow()
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        state=mode,
        prompt="select_account",  # optional; helps when multiple accounts
    )

    if st.button(label, use_container_width=True):
        st.markdown(
            f"<meta http-equiv='refresh' content='0; url={auth_url}'>",
            unsafe_allow_html=True,
        )
        st.stop()

def handle_google_callback() -> Optional[Dict[str, Any]]:
    auth_code = st.query_params.get("code")
    mode = st.query_params.get("state")

    if not auth_code:
        return None

    # prevent exchanging the same code twice (Streamlit reruns)
    if st.session_state.get("_last_google_code") == auth_code:
        st.query_params.clear()
        return None
    st.session_state["_last_google_code"] = auth_code

    try:
        flow = _google_flow()
        flow.fetch_token(code=auth_code)
        creds = flow.credentials

        # userinfo
        oauth_service = build(serviceName="oauth2", version="v2", credentials=creds)
        info = oauth_service.userinfo().get().execute()

        # IMPORTANT: id_token is more reliable from the token dict
        token_dict = getattr(flow, "oauth2session", None).token if getattr(flow, "oauth2session", None) else {}
        id_token = token_dict.get("id_token") or getattr(creds, "id_token", None)

        st.query_params.clear()

        return {
            "email": info.get("email"),
            "name": info.get("name"),
            "id_token": id_token,
            "mode": mode,
        }

    except Exception:
        st.query_params.clear()
        st.session_state.pop("_last_google_code", None)
        raise

def google_login_or_register() -> bool:
    try:
        payload = handle_google_callback()
    except Exception as e:
        st.error(f"❌ Google callback failed: {e}")
        return False

    if not payload:
        return False

    email = payload.get("email")
    id_token = payload.get("id_token")
    mode = payload.get("mode") or "login"

    st.write("DEBUG google mode:", mode)
    st.write("DEBUG google email:", email)
    st.write("DEBUG has id_token:", bool(id_token))

    if not email or not id_token:
        st.error("❌ Google auth failed (missing email or id_token).")
        return False

    exists = profile_exists(email)
    st.write("DEBUG profile exists:", exists)

    if mode == "login":
        if not exists:
            st.error("❌ This Google account is not registered yet. Please register first.")
            return False

    elif mode == "register":
        if not exists:
            create_profile(email=email)

    try:
        res = supabase.auth.sign_in_with_id_token({"provider": "google", "token": id_token})
        st.write("DEBUG supabase sign_in_with_id_token ok:", bool(res and res.user))

        if res and res.session and res.user:
            _token_mgr().set_token(
                email=res.user.email,
                access_token=res.session.access_token,
                refresh_token=res.session.refresh_token,
                provider="google",
            )
            return True

        st.error("❌ Supabase Google sign-in failed (no session returned).")
        return False

    except Exception as e:
        st.error(f"❌ Supabase Google sign-in failed: {e}")
        return False


def logout():
    try:
        supabase.auth.sign_out()
    except Exception:
        pass
    _token_mgr().delete_token()
    st.session_state.clear()
    st.rerun()