import streamlit as st

def render_header(selected_page):
    # --- Retrieve logged-in user info ---
    logged_in_user = st.session_state.get("logged_in_user")
    users = st.session_state.get("users", {})

    # Default placeholders (in case data not found)
    user_name = "Aida Affendi"
    user_initials = "AA"

    if logged_in_user and logged_in_user in users:
        user_data = users[logged_in_user]

        first_name = user_data.get("first_name", "")
        last_name = user_data.get("last_name", "")

        # Combine first and last name
        if first_name or last_name:
            user_name = f"{first_name} {last_name}".strip()

        # Generate initials (first letter of first and last name)
        if first_name and last_name:
            user_initials = f"{first_name[0].upper()}{last_name[0].upper()}"
        elif first_name:
            user_initials = first_name[0].upper()
        elif last_name:
            user_initials = last_name[0].upper()

    # --- HEADER LAYOUT ---
    col1, col2 = st.columns([4, 1])

    with col1:
        st.markdown("""
        <div style='display:flex; align-items:center; gap:10px;'>
            <div style='background-color:#2563eb; color:white; font-weight:bold; padding:8px 10px; border-radius:8px;'>FS</div>
            <h2 style='margin:0; font-size:1.3rem; color:#111827;'>FraudbAI</h2>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        # Make name, initials, and role clickable → redirect to Profile
        profile_clicked = st.button(
            f"👤 {user_name} ({user_initials})",
            key="header_profile_button",
            use_container_width=True
        )
        if profile_clicked:
            st.session_state["page"] = "Profile"
            st.rerun()
    st.divider()