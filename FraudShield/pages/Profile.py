import streamlit as st

def show():
    # --------------------------
    # PAGE HEADER
    # --------------------------
    st.title("👤 User Profile")
    st.caption("Manage your personal information and account credentials below.")

    # --------------------------
    # FETCH USER INFO FROM SESSION
    # --------------------------
    logged_in_email = st.session_state.get("logged_in_user")

    if not logged_in_email or "users" not in st.session_state:
        st.warning("⚠️ No active session. Please log in again.")
        st.session_state.page = "login"
        st.rerun()

    users = st.session_state["users"]
    user_data = users.get(logged_in_email, {})

    # Extract user details
    first_name = user_data.get("first_name", "")
    last_name = user_data.get("last_name", "")
    email = logged_in_email
    initials = f"{first_name[:1].upper()}{last_name[:1].upper()}" if first_name and last_name else "AA"
    role = st.session_state.get("user_role", "Fraud Analyst")

    # --------------------------
    # USER SUMMARY CARD
    # --------------------------
    st.markdown(f"""
    <div style='display:flex; align-items:center; gap:20px; margin-top:10px;'>
        <div style='width:80px; height:80px; border-radius:50%; 
                    background:linear-gradient(to bottom right, #3b82f6, #9333ea);
                    display:flex; align-items:center; justify-content:center; 
                    color:white; font-weight:bold; font-size:1.5rem;'>
            {initials}
        </div>
        <div>
            <h3 style='margin:0; font-size:1.2rem;'>{first_name} {last_name}</h3>
            <p style='margin:0; color:#6b7280;'>{role}</p>
            <span style='background:#dcfce7; color:#166534; padding:3px 8px; 
                        border-radius:6px; font-size:0.8rem;'>Active</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # --------------------------
    # PROFILE INFORMATION FORM
    # --------------------------
    with st.form("profile_form"):
        st.subheader("🧾 Personal Information")

        col1, col2 = st.columns(2)
        with col1:
            first_name_input = st.text_input("First Name", value=first_name)
            email_input = st.text_input("Email", value=email, disabled=True)
            department = st.selectbox(
                "Department",
                ["Security", "Finance", "Operations", "IT"],
                index=0
            )

        with col2:
            last_name_input = st.text_input("Last Name", value=last_name)
            phone = st.text_input("Phone", value="+60 12 345 6789")
            role = st.selectbox(
                "Role",
                ["Administrator", "Analyst", "Operator", "Viewer"],
                index=1
            )

        st.write("")
        c1, c2 = st.columns([1, 1])
        with c1:
            st.form_submit_button("Cancel")
        with c2:
            save = st.form_submit_button("💾 Save Changes", use_container_width=True)

        if save:
            # Update user data in session state
            user_data["first_name"] = first_name_input
            user_data["last_name"] = last_name_input
            users[logged_in_email] = user_data

            # Update display name and initials globally
            st.session_state["user_name"] = f"{first_name_input} {last_name_input}"
            st.session_state["user_initials"] = f"{first_name_input[0].upper()}{last_name_input[0].upper()}"

            st.toast("Profile updated successfully!", icon="✅")

    st.markdown("---")

    # --------------------------
    # PASSWORD CHANGE FORM
    # --------------------------
    with st.form("password_form"):
        st.subheader("🔑 Change Password")

        current = st.text_input("Current Password", type="password")
        new = st.text_input("New Password", type="password")
        confirm = st.text_input("Confirm New Password", type="password")

        st.write("")
        c1, c2 = st.columns([1, 1])
        with c1:
            st.form_submit_button("Cancel")
        with c2:
            change_pw = st.form_submit_button("🔒 Update Password", use_container_width=True)

        if change_pw:
            if not current or not new or not confirm:
                st.toast("Please fill in all password fields.", icon="⚠️")
            elif user_data.get("password") != current:
                st.toast("Current password incorrect!", icon="⚠️")
            elif new != confirm:
                st.toast("Passwords do not match!", icon="⚠️")
            else:
                user_data["password"] = new
                users[logged_in_email] = user_data
                st.toast("Password changed successfully!", icon="✅")

    st.divider()

    # --------------------------
    # Logout Section
    # --------------------------
    logout = st.button("Logout", type="primary", use_container_width=True)

    if logout:
        # Clear all session state keys (like a fresh restart)
        for key in list(st.session_state.keys()):
            del st.session_state[key]

        st.session_state["page"] = "login"
        st.toast("Successfully logged out.", icon="👋")
        st.rerun()