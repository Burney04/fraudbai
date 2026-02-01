import streamlit as st
from FraudShield.utils.supabase_client import supabase
from FraudShield.utils.auth import logout as do_logout


def _get_current_user():
    """Get current Supabase user from session_state, fallback to supabase.auth.get_user()."""
    user = st.session_state.get("user")

    if not user:
        try:
            user_res = supabase.auth.get_user()
            user = user_res.user if user_res else None
            if user:
                st.session_state.user = user
        except Exception:
            user = None

    return user


def _load_profile(email: str) -> dict:
    """Load user profile row from Supabase profiles table."""
    try:
        res = (
            supabase.table("profiles")
            .select("*")
            .eq("email", email)
            .limit(1)
            .execute()
        )
        if res and getattr(res, "data", None):
            return res.data[0] if len(res.data) else {}
    except Exception as e:
        st.error(f"❌ Failed to load profile: {e}")
    return {}


def _update_profile(email: str, payload: dict) -> bool:
    """Update user profile row in Supabase profiles table."""
    try:
        supabase.table("profiles").update(payload).eq("email", email).execute()
        return True
    except Exception as e:
        st.error(f"❌ Failed to update profile: {e}")
        return False


def show():
    # --------------------------
    # PAGE HEADER
    # --------------------------
    st.title("👤 User Profile")
    st.caption("Manage your personal information and account credentials below.")

    # --------------------------
    # FETCH USER INFO FROM SUPABASE SESSION
    # --------------------------
    user = _get_current_user()
    if not user:
        st.warning("⚠️ No active session. Please log in again.")
        st.session_state.page = "login"
        st.rerun()

    logged_in_email = user.email

    # --------------------------
    # LOAD PROFILE FROM SUPABASE TABLE
    # --------------------------
    profile = _load_profile(logged_in_email)

    # Extract profile details (fallbacks if missing)
    first_name = profile.get("first_name", "") or ""
    last_name = profile.get("last_name", "") or ""
    department_value = profile.get("department", "Security") or "Security"
    phone_value = profile.get("phone", "+60 12 345 6789") or "+60 12 345 6789"
    role_value = profile.get("role", "Analyst") or "Analyst"

    initials = (
        f"{first_name[:1].upper()}{last_name[:1].upper()}"
        if first_name and last_name
        else "AA"
    )

    # --------------------------
    # USER SUMMARY CARD
    # --------------------------
    st.markdown(
        f"""
        <div style='display:flex; align-items:center; gap:20px; margin-top:10px;'>
            <div style='width:80px; height:80px; border-radius:50%;
                        background:linear-gradient(to bottom right, #3b82f6, #9333ea);
                        display:flex; align-items:center; justify-content:center;
                        color:white; font-weight:bold; font-size:1.5rem;'>
                {initials}
            </div>
            <div>
                <h3 style='margin:0; font-size:1.2rem;'>{first_name} {last_name}</h3>
                <p style='margin:0; color:#6b7280;'>{role_value}</p>
                <span style='background:#dcfce7; color:#166534; padding:3px 8px;
                            border-radius:6px; font-size:0.8rem;'>Active</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    # --------------------------
    # PROFILE INFORMATION FORM
    # --------------------------
    departments = ["Security", "Finance", "Operations", "IT"]
    roles = ["Administrator", "Analyst", "Operator", "Viewer"]

    # Safe index helpers
    dept_index = departments.index(department_value) if department_value in departments else 0
    role_index = roles.index(role_value) if role_value in roles else 1

    with st.form("profile_form"):
        st.subheader("🧾 Personal Information")

        col1, col2 = st.columns(2)
        with col1:
            first_name_input = st.text_input("First Name", value=first_name, key="profile_first")
            st.text_input("Email", value=logged_in_email, disabled=True, key="profile_email")
            department_input = st.selectbox("Department", departments, index=dept_index, key="profile_dept")

        with col2:
            last_name_input = st.text_input("Last Name", value=last_name, key="profile_last")
            phone_input = st.text_input("Phone", value=phone_value, key="profile_phone")
            role_input = st.selectbox("Role", roles, index=role_index, key="profile_role")

        st.write("")
        c1, c2 = st.columns([1, 1])
        with c1:
            st.form_submit_button("Cancel")
        with c2:
            save = st.form_submit_button("💾 Save Changes", use_container_width=True, key="profile_save")

        if save:
            update_payload = {
                "first_name": first_name_input,
                "last_name": last_name_input,
            }

            ok = _update_profile(logged_in_email, update_payload)
            if ok:
                st.session_state["user_name"] = f"{first_name_input} {last_name_input}".strip()
                st.session_state["user_initials"] = (
                    f"{first_name_input[:1].upper()}{last_name_input[:1].upper()}"
                    if first_name_input and last_name_input
                    else "AA"
                )
                st.toast("Profile updated successfully!", icon="✅")
                st.rerun()

    st.markdown("---")

    # --------------------------
    # PASSWORD CHANGE FORM (SUPABASE AUTH)
    # --------------------------
    with st.form("password_form"):
        st.subheader("🔑 Change Password")

        # Supabase does not allow verifying "current password" directly.
        # Best practice: update password for active session OR use reset-email flow.
        new = st.text_input("New Password", type="password", key="pw_new")
        confirm = st.text_input("Confirm New Password", type="password", key="pw_confirm")

        st.write("")
        c1, c2 = st.columns([1, 1])
        with c1:
            st.form_submit_button("Cancel")
        with c2:
            change_pw = st.form_submit_button("🔒 Update Password", use_container_width=True, key="pw_update")

        if change_pw:
            if not new or not confirm:
                st.toast("Please fill in all password fields.", icon="⚠️")
            elif new != confirm:
                st.toast("Passwords do not match!", icon="⚠️")
            elif len(new) < 8:
                st.toast("Password should be at least 8 characters.", icon="⚠️")
            else:
                try:
                    supabase.auth.update_user({"password": new})
                    st.toast("Password updated successfully!", icon="✅")
                except Exception as e:
                    st.toast(f"Password update failed: {e}", icon="❌")

    st.divider()

    # --------------------------
    # LOGOUT
    # --------------------------
    if st.button("Logout", type="primary", use_container_width=True, key="profile_logout"):
        do_logout()