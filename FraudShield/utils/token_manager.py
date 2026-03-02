from datetime import datetime, timedelta
import jwt
from jwt import ExpiredSignatureError
import streamlit as st
import extra_streamlit_components as stx


class AuthTokenManager:
    def __init__(self, cookie_name: str, token_key: str, token_duration_days: int = 7):
        self.cookie_manager = stx.CookieManager()
        self.cookie_name = cookie_name
        self.token_key = token_key
        self.token_duration_days = token_duration_days

    def get_decoded_token(self):
        token = self.cookie_manager.get(self.cookie_name)
        if token is None:
            return None
        try:
            decoded = jwt.decode(token, self.token_key, algorithms=["HS256"])
            return decoded
        except ExpiredSignatureError:
            st.toast(":red[Session expired. Please login again.]")
            self.delete_token()
            return None

    def set_token(self, email: str, access_token: str, refresh_token: str, provider: str):
        exp = (datetime.now() + timedelta(days=self.token_duration_days)).timestamp()
        encoded = jwt.encode(
            {
                "email": email,
                "provider": provider,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "exp": exp,
            },
            self.token_key,
            algorithm="HS256",
        )
        self.cookie_manager.set(
            self.cookie_name,
            encoded,
            expires_at=datetime.fromtimestamp(exp),
        )

    def delete_token(self):
        try:
            self.cookie_manager.delete(self.cookie_name)
        except KeyError:
            pass