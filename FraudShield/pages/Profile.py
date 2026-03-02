import streamlit as st
from FraudShield.utils.supabase_client import supabase
from FraudShield.utils.auth import logout as do_logout
from FraudShield.utils.auth import set_display_name_in_session  # Add this import


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
        # Check if profile exists first
        res = supabase.table("profiles").select("email").eq("email", email).execute()
        
        if res.data:  # Profile exists, update it
            result = supabase.table("profiles").update(payload).eq("email", email).execute()
            if not result.data:
                st.error("❌ Update returned no data - profile might not exist")
                return False
            return True
        else:  # Profile doesn't exist, create it
            payload["email"] = email
            result = supabase.table("profiles").insert(payload).execute()
            if result.data:
                return True
            else:
                st.error("❌ Failed to create profile")
                return False
                
    except Exception as e:
        st.error(f"❌ Failed to update profile: {str(e)}")
        # Try to get more details about the error
        if hasattr(e, 'message'):
            st.error(f"Error details: {e.message}")
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
            cancel = st.form_submit_button("Cancel", use_container_width=True)
            if cancel:
                st.info("Changes cancelled")
        with c2:
            save = st.form_submit_button("💾 Save Changes", use_container_width=True, key="profile_save")

        if save:
            update_payload = {
                "first_name": first_name_input.strip(),
                "last_name": last_name_input.strip(),

            }
            
            # Validate input
            if not first_name_input.strip() or not last_name_input.strip():
                st.error("❌ First name and last name are required!")
            else:
                ok = _update_profile(logged_in_email, update_payload)
                if ok:
                    # Update session state
                    set_display_name_in_session(first_name_input.strip(), last_name_input.strip())
                    
                    st.success("✅ Profile updated successfully!")
                    st.balloons()
                    
                    # Add a small delay and rerun to show updated info
                    st.rerun()
                else:
                    st.error("❌ Failed to update profile. Please try again.")

    st.markdown("---")

    # --------------------------
    # PASSWORD CHANGE FORM (SUPABASE AUTH)
    # --------------------------
    with st.form("password_form"):
        st.subheader("🔑 Change Password")

        new = st.text_input("New Password", type="password", key="pw_new")
        confirm = st.text_input("Confirm New Password", type="password", key="pw_confirm")

        st.write("")
        c1, c2 = st.columns([1, 1])
        with c1:
            cancel_pw = st.form_submit_button("Cancel", use_container_width=True)
            if cancel_pw:
                st.info("Password change cancelled")
        with c2:
            change_pw = st.form_submit_button("🔒 Update Password", use_container_width=True, key="pw_update")

        if change_pw:
            if not new or not confirm:
                st.error("Please fill in all password fields.")
            elif new != confirm:
                st.error("Passwords do not match!")
            elif len(new) < 8:
                st.error("Password should be at least 8 characters.")
            else:
                try:
                    result = supabase.auth.update_user({"password": new})
                    if result:
                        st.success("✅ Password updated successfully!")
                        # Clear the password fields
                        st.rerun()
                    else:
                        st.error("❌ Password update failed.")
                except Exception as e:
                    st.error(f"❌ Password update failed: {str(e)}")

    st.divider()

    # --------------------------
    # DEBUG SECTION (Temporary)
    # --------------------------
    if st.checkbox("Show Debug Info", key="debug_checkbox"):
        st.subheader("🔧 Debug Information")

        st.write("**Current Session State:**")
        st.json({
            "user_name": st.session_state.get("user_name"),
            "user_initials": st.session_state.get("user_initials"),
            "email": logged_in_email,
            "profile_data": profile
        })
        
        # Test database connection
        if st.button("Test Profile Load", key="test_load"):
            test_profile = _load_profile(logged_in_email)
            st.write("**Loaded Profile:**", test_profile)
            
        if st.button("Clear Session Cache", key="clear_cache"):
            keys_to_clear = ["user_name", "user_initials"]
            for key in keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

    st.divider()

    # --------------------------
    # LOGOUT
    # --------------------------
    if st.button("Logout", type="primary", use_container_width=True, key="profile_logout"):
        do_logout()