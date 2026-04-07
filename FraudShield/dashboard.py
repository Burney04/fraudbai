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

    # Initialize scroll tracking
    if "previous_page" not in st.session_state:
        st.session_state.previous_page = None
    if "scroll_reset_counter" not in st.session_state:
        st.session_state.scroll_reset_counter = 0

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

    # --------------------------------------------------
    # 3.5️⃣ CHECK QUERY PARAMETERS FOR NAVIGATION
    # --------------------------------------------------
    if "page" in st.query_params:
        target_page = st.query_params["page"]
        page_mapping = {
            "Drill-Down Inspection": "🔍 Drill-Down Inspection",
            "drill_down": "🔍 Drill-Down Inspection",
            "filter_cases": "🗂️ Filter Cases",
            "case_validation": "✅ Case Validation"
        }
        
        mapped_page = page_mapping.get(target_page, target_page)
        
        if mapped_page in pages:
            st.session_state.active_page = mapped_page
            st.query_params.clear()
    
    # Check for case_id parameter
    if "case_id" in st.query_params and st.session_state.active_page == "🔍 Drill-Down Inspection":
        st.session_state.selected_case_id = st.query_params["case_id"]

    if "active_page" not in st.session_state:
        st.session_state.active_page = list(pages.keys())[0]

    # --------------------------------------------------
    # 3.6️⃣ CHECK FOR PAGE CHANGE AND RESET SCROLL
    # --------------------------------------------------
    page_changed = st.session_state.previous_page != st.session_state.active_page
    
    if page_changed:
        # Increment counter to force DOM update
        st.session_state.scroll_reset_counter += 1
        st.session_state.previous_page = st.session_state.active_page
        
        # Force scroll to top using multiple methods
        # Empty containers to force browser focus reset
        for _ in range(2):
            st.empty()
        
        # Add an invisible element at the top with unique ID based on counter
        unique_id = f"scroll-top-{st.session_state.scroll_reset_counter}"
        st.markdown(f'<div id="{unique_id}" style="position: absolute; top: 0;"></div>', unsafe_allow_html=True)
        
        # Force scroll to that element using JavaScript
        st.components.v1.html(
            f"""
            <script>
                // Wait for page to load
                setTimeout(function() {{
                    var element = parent.document.getElementById('{unique_id}');
                    if (element) {{
                        element.scrollIntoView({{behavior: 'instant', block: 'start'}});
                    }}
                    // Also scroll the main container
                    var mainContainer = parent.document.querySelector('.main');
                    if (mainContainer) {{
                        mainContainer.scrollTop = 0;
                    }}
                    // Scroll window as well
                    window.parent.scrollTo(0, 0);
                }}, 50);
                
                // Double-check after a longer delay
                setTimeout(function() {{
                    var mainContainer = parent.document.querySelector('.main');
                    if (mainContainer && mainContainer.scrollTop > 0) {{
                        mainContainer.scrollTop = 0;
                        window.parent.scrollTo(0, 0);
                    }}
                }}, 150);
            </script>
            """,
            height=0
        )

    # --------------------------------------------------
    # 4️⃣ SIDEBAR BUTTONS
    # --------------------------------------------------
    for page_name in pages.keys():
        if st.session_state.active_page == page_name:
            if st.sidebar.button(
                page_name,
                key=f"nav_{page_name}",
                use_container_width=True,
                type="primary"
            ):
                pass
        else:
            if st.sidebar.button(
                page_name,
                key=f"nav_{page_name}",
                use_container_width=True,
                type="secondary"
            ):
                st.session_state.active_page = page_name
                st.rerun()

    # --------------------------------------------------
    # 5️⃣ HEADER
    # --------------------------------------------------
    render_header("Dashboard")

    user_email = st.session_state.user.email
    st.caption(f"Logged in as: **{user_email}**")

    # --------------------------------------------------
    # 6️⃣ PAGE RENDER
    # --------------------------------------------------
    pages[st.session_state.active_page]()

    # --------------------------------------------------
    # 7️⃣ FOOTER
    # --------------------------------------------------
    st.sidebar.markdown("---")
    st.sidebar.caption("© 2025 FraudbAI | Intelligent Fraud Analytics")