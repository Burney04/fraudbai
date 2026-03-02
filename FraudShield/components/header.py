import streamlit as st
from FraudShield.utils.supabase_client import supabase

@st.cache_data(ttl=300)
def _load_profile_by_email(email: str) -> dict:
    """Load user profile from Supabase with caching."""
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
    except Exception as e:
        # Log error but don't crash
        print(f"Error loading profile: {e}")
    return {}

def _compute_name_and_initials(first_name: str, last_name: str):
    """Generate display name and initials from first/last name."""
    first_name = (first_name or "").strip()
    last_name = (last_name or "").strip()

    full_name = f"{first_name} {last_name}".strip()
    if not full_name:
        full_name = "user_1"

    if first_name and last_name:
        initials = f"{first_name[0].upper()}{last_name[0].upper()}"
    elif first_name:
        initials = first_name[0].upper()
    elif last_name:
        initials = last_name[0].upper()
    else:
        initials = "U1"

    return full_name, initials

def render_header(selected_page):
    """Render the app header with user info and navigation."""
    # 1) Prefer values already stored in session_state
    user_name = st.session_state.get("user_name", "User 1")
    user_initials = st.session_state.get("user_initials", "U1")

    # 2) If not available yet, try to load from Supabase
    if not user_name or not user_initials or user_name == "User 1":
        user = st.session_state.get("user")

        if not user:
            try:
                user_res = supabase.auth.get_user()
                user = user_res.user if user_res else None
                if user:
                    st.session_state["user"] = user
            except Exception:
                user = None

        email = getattr(user, "email", None) if user else None
        if email:
            profile = _load_profile_by_email(email)
            first_name = profile.get("first_name", "")
            last_name = profile.get("last_name", "")

            user_name, user_initials = _compute_name_and_initials(first_name, last_name)

            st.session_state["user_name"] = user_name
            st.session_state["user_initials"] = user_initials

    # 3) Final fallback
    if not user_name or user_name == "User 1":
        user_name = "User"
    if not user_initials or user_initials == "U1":
        user_initials = "U"

    # --- HEADER LAYOUT ---
    col1, col2 = st.columns([4, 1])

    with col1:
        st.markdown(
            """
            <div style='display:flex; align-items:center; gap:10px;'>
                <div style='background-color:#2563eb; color:white; font-weight:bold; padding:8px 10px; border-radius:8px;'>FS</div>
                <h2 style='margin:0; font-size:1.3rem; color:#111827;'>FraudbAI</h2>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        # Create a clickable profile button
        profile_clicked = st.button(
            f"👤 {user_name}",
            key="header_profile_button",
            use_container_width=True,
            help="Click to go to your profile"
        )
                
        if profile_clicked:
            # Set the active page to Profile (matching the sidebar)
            st.session_state["active_page"] = "👤 Profile"
            st.rerun()

    st.divider()