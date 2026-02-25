import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Do NOT strip proxy env vars on Streamlit Cloud (can break networking/DNS)
# for key in ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"]:
#     os.environ.pop(key, None)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Fallback to Streamlit secrets when running on Streamlit Cloud
if not SUPABASE_URL or not SUPABASE_KEY:
    try:
        import streamlit as st
        SUPABASE_URL = SUPABASE_URL or st.secrets.get("SUPABASE_URL")
        SUPABASE_KEY = SUPABASE_KEY or st.secrets.get("SUPABASE_KEY")
    except Exception:
        pass

# Strip accidental spaces (very common issue)
if SUPABASE_URL:
    SUPABASE_URL = str(SUPABASE_URL).strip()
if SUPABASE_KEY:
    SUPABASE_KEY = str(SUPABASE_KEY).strip()

# Optional debug (remove later)
print("DEBUG SUPABASE_URL:", SUPABASE_URL)
print("DEBUG SUPABASE_KEY exists:", bool(SUPABASE_KEY))

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Missing SUPABASE_URL or SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)