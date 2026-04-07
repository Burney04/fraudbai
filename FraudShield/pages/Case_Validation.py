import streamlit as st
import pandas as pd
from FraudShield.utils.supabase_client import supabase
from datetime import datetime

def show():
    # --- Load Data from Supabase (Load all cases without ordering to show older data) ---
    @st.cache_data(ttl=60)  # Cache for 60 seconds
    def load_fraud_cases():
        """Load fraud cases from Supabase (no date ordering to show older cases)."""
        try:
            # Remove ORDER BY to see all cases including older ones like FR-2025-4000
            response = supabase.table("fraud_cases") \
                .select("*") \
                .limit(1000) \
                .execute()
            
            if response.data:
                df = pd.DataFrame(response.data)
                # Ensure case_id is properly formatted as string
                if 'case_id' in df.columns:
                    df['case_id'] = df['case_id'].astype(str)
                
                # Sort by case_id numerically to show smaller IDs first
                # Extract numeric part from case_id (e.g., "FR-2025-4000" -> 4000)
                df['case_id_num'] = df['case_id'].str.extract(r'(\d+)$').astype(int)
                df = df.sort_values('case_id_num').drop('case_id_num', axis=1)
                
                return df.to_dict('records')
            else:
                return []
        except Exception as e:
            st.error(f"Error loading fraud cases: {e}")
            return []

    # Initialize session state
    def init_state():
        """Initialize Streamlit session state variables."""
        if "cases" not in st.session_state:
            st.session_state.cases = load_fraud_cases()
        if "selected_case_id" not in st.session_state:
            st.session_state.selected_case_id = None
        if "notes" not in st.session_state:
            st.session_state.notes = ""
        if "pending_page" not in st.session_state:
            st.session_state.pending_page = 0  # 0-indexed page number

    # --- Helper Functions ---
    def extract_risk_score(risk_display):
        """Extract numeric risk score from risk display."""
        try:
            if not risk_display:
                return 0.5
            
            risk_str = str(risk_display)
            
            # Try to find percentage format (e.g., "90%")
            if '%' in risk_str:
                import re
                percentage_match = re.search(r'(\d+)%', risk_str)
                if percentage_match:
                    return int(percentage_match.group(1)) / 100
            
            # Try to find decimal in parentheses (e.g., "High (0.90)")
            if '(' in risk_str and ')' in risk_str:
                decimal_str = risk_str.split('(')[1].split(')')[0]
                return float(decimal_str)
            
            return 0.5
        except:
            return 0.5

    def handle_validate(case_id, decision):
        """Update case validation status."""
        # Update local session state
        for case_ in st.session_state.cases:
            if case_["case_id"] == case_id:
                case_["actual_fraud"] = decision
                
                # Update in Supabase
                try:
                    supabase.table("fraud_cases") \
                        .update({"actual_fraud": decision}) \
                        .eq("case_id", case_id) \
                        .execute()
                except Exception as e:
                    st.error(f"Error updating database: {e}")

        case_item = next((c for c in st.session_state.cases if c["case_id"] == case_id), None)
        
        # Get appropriate message based on decision
        if decision == "confirmed":
            messages = f"✅ Case {case_id} confirmed as fraud."
            icon = "✅"
        elif decision == "rejected":
            messages = f"🟢 Case {case_id} marked as legitimate."
            icon = "🟢"
        else:  # escalated
            messages = f"🟣 Case {case_id} escalated."
            icon = "🟣"

        if case_item:
            st.toast(messages, icon=icon)

        # Reset form state
        st.session_state.notes = ""
        st.session_state.selected_case_id = None

    def refresh_data():
        """Manually refresh data from Supabase."""
        # Clear cache and reload
        st.cache_data.clear()
        st.session_state.cases = load_fraud_cases()
        st.session_state.pending_page = 0  # Reset to first page
        st.rerun()

    # --- Page Render Function ---
    def render():
        """Main UI for Validation Queue Page."""
        init_state()

        cases = st.session_state.cases
        selected_case_id = st.session_state.selected_case_id
        notes = st.session_state.notes

        # --- Header ---
        st.title("🧾 Fraud Case Validation")
        
        # Display info about data limit
        st.caption(f"📊 Showing {len(cases)} cases from database (ordered by Case ID ascending)")
        
        # Refresh button
        col_title, col_refresh = st.columns([6, 1])
        with col_refresh:
            if st.button("🔄 Refresh Data", use_container_width=True):
                refresh_data()

        st.divider()
        
        # --- Validation Summary Section ---
        st.subheader("📊 Validation Summary")
        
        # Calculate statistics
        total_cases = len(cases)
        
        # Segregate cases based on risk score threshold for display purposes
        confirmed_cases = []
        pending_ambiguous_cases = []
        
        for case in cases:
            risk_score = extract_risk_score(case.get('risk_display', 'N/A'))
            
            # Check if case is confirmed (has actual_fraud value OR risk score > 90%)
            is_confirmed = (case.get('actual_fraud') in ['confirmed', 'rejected', 'escalated']) or (risk_score > 0.90)
            
            if is_confirmed:
                confirmed_cases.append(case)
            else:
                pending_ambiguous_cases.append(case)
        
        # Count validation statuses (from actual_fraud field)
        manually_confirmed_count = sum(1 for c in cases if c.get('actual_fraud') == 'confirmed')
        legitimate_count = sum(1 for c in cases if c.get('actual_fraud') == 'rejected')
        escalated_count = sum(1 for c in cases if c.get('actual_fraud') == 'escalated')
        
        # Display metrics in 4 columns
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("⏳ Pending Validation", len(pending_ambiguous_cases))
        with col2:
            st.metric("✅ Confirmed Cases", len(confirmed_cases))
        with col3:
            st.metric("🟢 Legitimate (Rejected)", legitimate_count)
        with col4:
            st.metric("🟣 Escalated", escalated_count)
        
        st.divider()
        
        # --- Tabs for Cases ---
        tab1, tab2 = st.tabs(["⚠️ Pending Cases", "✅ Validated Cases"])
        
        # --- Tab 1: Pending Cases ---
        with tab1:
            st.caption(f"Cases that need manual validation (Total: {len(pending_ambiguous_cases)} cases)")
            
            if pending_ambiguous_cases:
                # Pagination settings - changed from 10 to 7
                CARDS_PER_PAGE = 7
                total_pages = (len(pending_ambiguous_cases) + CARDS_PER_PAGE - 1) // CARDS_PER_PAGE
                
                # Ensure page is within bounds
                if st.session_state.pending_page >= total_pages:
                    st.session_state.pending_page = total_pages - 1
                if st.session_state.pending_page < 0:
                    st.session_state.pending_page = 0
                
                # Get current page cases
                start_idx = st.session_state.pending_page * CARDS_PER_PAGE
                end_idx = min(start_idx + CARDS_PER_PAGE, len(pending_ambiguous_cases))
                current_cases = pending_ambiguous_cases[start_idx:end_idx]
                
                # Layout: Queue (Left) + Validation Panel (Right)
                col_left, col_right = st.columns([2, 1])
                
                # --- Left Column: Pending Cases Cards (Paginated) ---
                with col_left:
                    # Display page info
                    st.markdown(f"**Page {st.session_state.pending_page + 1} of {total_pages}** (Showing {start_idx + 1}-{end_idx} of {len(pending_ambiguous_cases)} cases)")
                    
                    # Display cards for current page
                    for idx, case_ in enumerate(current_cases):
                        risk_score = extract_risk_score(case_.get('risk_display', 'N/A'))
                        risk_percentage = int(risk_score * 100)
                        
                        # Determine risk badge color based on risk score
                        if risk_percentage >= 80:
                            badge_color = "#DC2626"  # Red for high risk
                            badge_bg = "#FEE2E2"
                            risk_badge = "🔴 High Risk"
                        elif risk_percentage >= 60:
                            badge_color = "#D97706"  # Orange for medium risk
                            badge_bg = "#FEF3C7"
                            risk_badge = "🟠 Medium Risk"
                        else:
                            badge_color = "#059669"  # Green for low risk
                            badge_bg = "#D1FAE5"
                            risk_badge = "🟢 Low Risk"
                        
                        # Highlight selected card border
                        if selected_case_id == case_["case_id"]:
                            border_color = "#3B82F6"
                            border_width = "2px"
                            selected_badge = " ✓ SELECTED"
                        else:
                            border_color = "#E5E7EB"
                            border_width = "1px"
                            selected_badge = ""
                        
                        # Create a container for each card
                        with st.container():
                            st.markdown(
                                f"""
                                <div style='
                                    background: #FFFFFF;
                                    border: {border_width} solid {border_color};
                                    border-radius: 12px;
                                    padding: 16px;
                                    margin-bottom: 12px;
                                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                                    transition: all 0.2s ease;
                                '>
                                    <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;'>
                                        <div>
                                            <span style='font-size: 1rem; font-weight: 700; color: #1F2937;'>
                                                📌 {case_['case_id']}{selected_badge}
                                            </span>
                                        </div>
                                        <div>
                                            <span style='
                                                background: {badge_bg};
                                                color: {badge_color};
                                                padding: 4px 12px;
                                                border-radius: 20px;
                                                font-size: 0.75rem;
                                                font-weight: 600;
                                            '>
                                                {risk_badge}
                                            </span>
                                        </div>
                                    </div>
                                    <div style='margin-top: 8px; display: flex; gap: 15px; flex-wrap: wrap;'>
                                        <span style='color: #6B7280; font-size: 0.85rem;'>
                                            💰 <strong>{case_.get('amount_formatted', 'N/A')}</strong>
                                        </span>
                                        <span style='color: #6B7280; font-size: 0.85rem;'>
                                            📊 <strong>{risk_percentage}%</strong> Risk Score
                                        </span>
                                    </div>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )
                            
                            # Selection button
                            if st.button(
                                f"Select {case_['case_id']}",
                                key=f"select_btn_{case_['case_id']}_{start_idx + idx}",
                                use_container_width=True,
                                type="secondary" if selected_case_id != case_["case_id"] else "primary"
                            ):
                                st.session_state.selected_case_id = case_["case_id"]
                                st.rerun()
                    
                    # Pagination controls with page number input
                    if total_pages > 1:
                        st.markdown("---")
                        
                        # Create 3 columns for pagination controls
                        col_prev, col_page_input, col_next = st.columns([1, 2, 1])
                        
                        # Previous button
                        with col_prev:
                            if st.button("◀ Previous", use_container_width=True, disabled=(st.session_state.pending_page == 0)):
                                st.session_state.pending_page -= 1
                                st.rerun()
                        
                        # Page number input box
                        with col_page_input:
                            # Create a row with number input and go button
                            input_col1, input_col2 = st.columns([3, 1])
                            with input_col1:
                                page_number = st.number_input(
                                    "Go to page",
                                    min_value=1,
                                    max_value=total_pages,
                                    value=st.session_state.pending_page + 1,
                                    step=1,
                                    label_visibility="collapsed",
                                    key="page_number_input"
                                )
                            with input_col2:
                                if st.button("Go", use_container_width=True, key="go_to_page"):
                                    if 1 <= page_number <= total_pages:
                                        st.session_state.pending_page = page_number - 1
                                        st.rerun()
                        
                        # Next button
                        with col_next:
                            if st.button("Next ▶", use_container_width=True, disabled=(st.session_state.pending_page >= total_pages - 1)):
                                st.session_state.pending_page += 1
                                st.rerun()
                        
                        # Show current page info
                        st.markdown(f"<div style='text-align: center; margin-top: 8px; font-size: 0.85rem; color: #666;'>Page {st.session_state.pending_page + 1} of {total_pages}</div>", unsafe_allow_html=True)
                
                # --- Right Column: Validation Panel ---
                with col_right:
                    st.markdown("### 🧩 Validation Decision")
                    
                    selected_case = next((c for c in pending_ambiguous_cases if c["case_id"] == selected_case_id), None)
                    
                    if selected_case:
                        risk_score = extract_risk_score(selected_case.get('risk_display', 'N/A'))
                        risk_percentage = int(risk_score * 100)
                        
                        # Determine risk level for display
                        if risk_percentage >= 80:
                            risk_level_display = "🔴 High Risk"
                            risk_color = "#DC2626"
                        elif risk_percentage >= 60:
                            risk_level_display = "🟠 Medium Risk"
                            risk_color = "#D97706"
                        else:
                            risk_level_display = "🟢 Low Risk"
                            risk_color = "#059669"
                        
                        st.markdown(f"#### Selected Case: `{selected_case['case_id']}`")
                        
                        # Display case details in a clean format (only Amount and Risk Score)
                        detail_col1, detail_col2 = st.columns(2)
                        with detail_col1:
                            st.write("**💰 Amount:**")
                            st.write(selected_case.get('amount_formatted', 'N/A'))
                        with detail_col2:
                            st.write("**📊 Risk Score:**")
                            st.markdown(f"<span style='color: {risk_color}; font-weight: 600;'>{risk_percentage}% ({risk_level_display})</span>", unsafe_allow_html=True)
                        
                        st.markdown("---")
                        
                        # Notes field
                        notes = st.text_area(
                            "💬 Feedback Notes",
                            value=st.session_state.notes,
                            placeholder="Add your feedback or observations here...",
                            height=100,
                            key="validation_notes"
                        )
                        st.session_state.notes = notes
                        
                        st.markdown("---")
                        
                        # Decision buttons
                        st.markdown("**Choose Action:**")
                        col_a, col_b, col_c = st.columns(3)
                        with col_a:
                            if st.button("✅ Confirm Fraud", use_container_width=True, type="primary"):
                                handle_validate(selected_case["case_id"], "confirmed")
                        with col_b:
                            if st.button("🟢 Legitimate", use_container_width=True):
                                handle_validate(selected_case["case_id"], "rejected")
                        with col_c:
                            if st.button("🟣 Escalate", use_container_width=True):
                                handle_validate(selected_case["case_id"], "escalated")
                        
                        st.markdown("---")
                        
                        # Inspect button - Using query params for navigation
                        if st.button("🔍 Inspect Case in Detail", use_container_width=True, key=f"inspect_btn_{selected_case['case_id']}"):
                            st.session_state.selected_case_id = selected_case["case_id"]
                            # Use query parameters to trigger navigation
                            st.query_params["page"] = "Drill-Down Inspection"
                            st.query_params["case_id"] = selected_case["case_id"]
                            st.rerun()
                    else:
                        st.info("👈 Select a case from the left panel to begin validation")
            else:
                st.info("📭 No pending cases. All cases have been confirmed.")
        
        # --- Tab 2: Validated Cases ---
        with tab2:
            st.caption(f"All validated cases (auto-confirmed + manually validated) (Total: {len(confirmed_cases)} cases)")
            
            if confirmed_cases:
                # Create a DataFrame for display with additional columns
                display_data = []
                for case in confirmed_cases:
                    risk_display = case.get('risk_display', 'N/A')
                    risk_score = extract_risk_score(risk_display)
                    risk_percentage = f"{int(risk_score * 100)}%"
                    
                    # Determine validation status
                    validation_status = case.get('actual_fraud', 'N/A')
                    if validation_status == 'confirmed':
                        validated_status = "Confirmed Fraud"
                    elif validation_status == 'rejected':
                        validated_status = "Legitimate"
                    elif validation_status == 'escalated':
                        validated_status = "Escalated"
                    elif risk_score > 0.90:
                        validated_status = "Auto-Confirmed"
                    else:
                        validated_status = "N/A"
                    
                    display_data.append({
                        "Case ID": case.get('case_id', 'N/A'),
                        "Timestamp": case.get('created_at', 'N/A'),
                        "Amount": case.get('amount_formatted', 'N/A'),
                        "Risk Score": risk_percentage,
                        "Sentiment": case.get('sentiment', 'N/A'),
                        "Fraud Terms": case.get('fraud_terms', 'N/A'),
                        "Complaint Link": case.get('complaint_link', 'N/A'),
                        "Customer History": case.get('customer_history', 'N/A'),
                        "Model Prediction": "N/A",  # Placeholder
                        "Validated": validated_status,
                        "SHAP": "N/A",  # Placeholder
                        "Key Reason": "N/A",  # Placeholder
                    })
                
                df_display = pd.DataFrame(display_data)
                
                # Show the table with new columns
                st.dataframe(
                    df_display,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Case ID": st.column_config.TextColumn("Case ID", width="medium"),
                        "Timestamp": st.column_config.DatetimeColumn("Timestamp", width="medium"),
                        "Amount": st.column_config.TextColumn("Amount", width="small"),
                        "Risk Score": st.column_config.TextColumn("Risk Score", width="small"),
                        "Sentiment": st.column_config.TextColumn("Sentiment", width="small"),
                        "Fraud Terms": st.column_config.TextColumn("Fraud Terms", width="medium"),
                        "Complaint Link": st.column_config.TextColumn("Complaint Link", width="medium"),
                        "Customer History": st.column_config.TextColumn("Customer History", width="medium"),
                        "Model Prediction": st.column_config.TextColumn("Model Prediction", width="small"),
                        "Validated": st.column_config.TextColumn("Validated", width="small"),
                        "SHAP": st.column_config.TextColumn("SHAP", width="small"),
                        "Key Reason": st.column_config.TextColumn("Key Reason", width="large"),
                    }
                )
                
                # Export button for confirmed cases
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    if st.button("📥 Export Confirmed Cases to CSV", use_container_width=True):
                        export_df = pd.DataFrame(display_data)
                        csv = export_df.to_csv(index=False)
                        st.download_button(
                            label="Download CSV",
                            data=csv,
                            file_name=f"confirmed_cases_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv",
                            key="export_confirmed"
                        )
            else:
                st.info("📭 No confirmed cases yet. Cases will appear here when confirmed (auto or manual).")

    render()