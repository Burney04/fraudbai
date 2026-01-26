import streamlit as st
from FraudShield.components.header import render_header
from FraudShield.utils.session import init_session_state
from FraudShield.utils.supabase_client import supabase

# --- Import all page functions ---
from FraudShield.pages.Reports import render_reports
from FraudShield.pages.Case_Validation import show as show_case_validation
from FraudShield.pages.Case_Drill_Down_Inspection import show as show_case_drilldown
from FraudShield.pages.Filter_Cases import show as show_filter_cases
from FraudShield.pages.Model_Insights import show as show_model_insights
from FraudShield.pages.Profile import show as show_profile


st.set_page_config(
    page_title="FraudbAI",
    page_icon="🛡️",
    layout="wide"
)

def show():
    # --------------------------------------------------
    # 1️⃣ INIT SESSION
    # --------------------------------------------------
    init_session_state()

    # --------------------------------------------------
    # 2️⃣ AUTHORITATIVE AUTH CHECK (Supabase)
    # --------------------------------------------------
    if not st.session_state.is_authenticated or not st.session_state.user:
        st.session_state.page = "login"
        st.rerun()
        
    # --------------------------------------------------
    # 3️⃣ SIDEBAR NAVIGATION
    # --------------------------------------------------
    st.sidebar.title("🧭 Navigation")

    pages = {
        "📊 Reports": render_reports,
        "✅ Case Validation": show_case_validation,
        "🔍 Drill-Down Inspection": show_case_drilldown,
        "🗂️ Filter Cases": show_filter_cases,
        "🧠 Model Insights": show_model_insights,
        "👤 Profile": show_profile,
    }

    if "active_page" not in st.session_state:
        st.session_state.active_page = list(pages.keys())[0]

    selected = st.sidebar.radio(
        "Select a page:",
        options=list(pages.keys()),
        index=list(pages.keys()).index(st.session_state.active_page),
    )

    st.session_state.active_page = selected

    # --------------------------------------------------
    # 4️⃣ HEADER
    # --------------------------------------------------
    render_header("Dashboard")

    user_email = st.session_state.user.email
    st.caption(f"Logged in as: **{user_email}**")

    # --------------------------------------------------
    # 5️⃣ PAGE RENDER
    # --------------------------------------------------
    pages[selected]()

    # --------------------------------------------------
    # 6️⃣ FOOTER
    # --------------------------------------------------
    st.sidebar.markdown("---")
    st.sidebar.caption("© 2025 FraudbAI | Intelligent Fraud Analytics")