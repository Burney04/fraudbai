from datetime import datetime, timedelta
import time
import jwt
from jwt import ExpiredSignatureError
import streamlit as st
import extra_streamlit_components as stx


def _get_cookie_manager(cm_key: str):
    """
    CookieManager is a Streamlit component (widget-like).
    Use a unique key to avoid 'init' collisions.
    """
    if "_cookie_managers" not in st.session_state:
        st.session_state["_cookie_managers"] = {}

    if cm_key not in st.session_state["_cookie_managers"]:
        st.session_state["_cookie_managers"][cm_key] = stx.CookieManager(key=cm_key)

    return st.session_state["_cookie_managers"][cm_key]


class AuthTokenManager:
    def __init__(self, cookie_name: str, token_key: str, token_duration_days: int = 7):
        self.cookie_name = cookie_name
        self.token_key = token_key
        self.token_duration_days = token_duration_days

        # Unique key per cookie_name to prevent duplicate internal key='init'
        self.cookie_manager = _get_cookie_manager(f"cookie_mgr_{cookie_name}")

    def get_decoded_token(self):
        """Retrieve and decode the token from cookie."""
        try:
            # Ensure cookie manager is ready
            self.cookie_manager.get_all()
            time.sleep(0.05)  # Small delay for frontend sync
        except Exception:
            pass  # Silently continue if get_all fails

        try:
            token = self.cookie_manager.get(self.cookie_name)
        except Exception:
            # Cookie might not exist yet
            return None

        if token is None:
            return None

        try:
            decoded = jwt.decode(token, self.token_key, algorithms=["HS256"])
            return decoded
        except ExpiredSignatureError:
            st.toast(":red[Session expired. Please login again.]")
            self.delete_token()
            return None
        except jwt.InvalidTokenError:
            # Token is malformed or invalid
            self.delete_token()
            return None

    def set_token(self, email: str, access_token: str, refresh_token: str, provider: str):
        """Create and store a new token in cookie."""
        exp = (datetime.now() + timedelta(days=self.token_duration_days)).timestamp()
        
        payload = {
            "email": email,
            "provider": provider,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "exp": exp,
        }
        
        encoded = jwt.encode(
            payload,
            self.token_key,
            algorithm="HS256",
        )
        
        try:
            self.cookie_manager.set(
                self.cookie_name,
                encoded,
                expires_at=datetime.fromtimestamp(exp),
                key=f"set_{self.cookie_name}_{int(time.time())}",  # Add unique key to prevent conflicts
            )
        except Exception as e:
            st.error(f"Failed to set cookie: {e}")

    def delete_token(self):
        """Remove the token cookie."""
        try:
            self.cookie_manager.delete(self.cookie_name)
        except KeyError:
            # Cookie doesn't exist - that's fine
            pass
        except Exception as e:
            # Log but don't crash
            print(f"Error deleting cookie: {e}")

    def refresh_token(self, new_access_token: str, new_refresh_token: str = None):
        """Update an existing token with new credentials while preserving metadata."""
        try:
            old_token = self.get_decoded_token()
            if old_token:
                self.set_token(
                    email=old_token.get("email"),
                    access_token=new_access_token,
                    refresh_token=new_refresh_token or old_token.get("refresh_token"),
                    provider=old_token.get("provider", "app"),
                )
                return True
        except Exception:
            pass
        return False