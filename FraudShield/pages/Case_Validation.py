import streamlit as st
import pandas as pd
from FraudShield.utils.supabase_client import supabase
from datetime import datetime

def show():
    # --- Load Data from Supabase ---
    @st.cache_data(ttl=60)  # Cache for 60 seconds
    def load_fraud_cases():
        """Load fraud cases from Supabase."""
        try:
            response = supabase.table("fraud_cases") \
                .select("*") \
                .order("transaction_date", desc=True) \
                .execute()
            
            if response.data:
                df = pd.DataFrame(response.data)
                # Ensure case_id is properly formatted as string
                if 'case_id' in df.columns:
                    df['case_id'] = df['case_id'].astype(str)
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

    # --- Helper Functions ---
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
        st.session_state.cases = load_fraud_cases()
        st.cache_data.clear()
        st.rerun()

    # --- Page Render Function ---
    def render():
        """Main UI for Validation Queue Page."""
        init_state()

        cases = st.session_state.cases
        selected_case_id = st.session_state.selected_case_id
        notes = st.session_state.notes

        # All cases
        pending_cases = cases

        # --- Header ---
        st.title("🧾 Fraud Case Validation")
        
        # Refresh button
        col_title, col_refresh = st.columns([6, 1])
        with col_refresh:
            if st.button("🔄 Refresh Data", use_container_width=True):
                refresh_data()

        st.divider()
        
        # --- Case Validation Section ---
        st.subheader("🔍 Case Validation")
        
        col_left, col_right = st.columns([1, 1])

        # --- Left Column: Case Selector ---
        with col_left:
            st.markdown("### Select a Case")
            
            # Create a dropdown for case selection using actual case IDs from database
            if pending_cases:
                case_options = {f"{c['case_id']} - {c.get('amount_formatted', 'N/A')} ({c.get('risk_display', 'N/A')})": c['case_id'] 
                               for c in pending_cases}
                
                selected_display = st.selectbox(
                    "Choose a case to validate:",
                    options=list(case_options.keys()),
                    index=None,
                    placeholder="Select a case...",
                    key="case_selector"
                )
                
                if selected_display:
                    selected_case_id = case_options[selected_display]
                    st.session_state.selected_case_id = selected_case_id

                # Show instruction message below dropdown when no case is selected
                if not st.session_state.selected_case_id:
                    st.info("👆 Select a case from the dropdown above to begin validation")

                # Show selected case details
                if st.session_state.selected_case_id:
                    selected_case = next((c for c in pending_cases if c["case_id"] == st.session_state.selected_case_id), None)
                    
                    if selected_case:
                        st.markdown("### Selected Case Details")
                        
                        # Create a nice details view with actual database values
                        details_df = pd.DataFrame([
                            {"Field": "Case ID", "Value": selected_case.get('case_id', 'N/A')},
                            {"Field": "Date", "Value": selected_case.get('transaction_date', 'N/A')},
                            {"Field": "Amount", "Value": selected_case.get('amount_formatted', 'N/A')},
                            {"Field": "Risk", "Value": selected_case.get('risk_display', 'N/A')},
                            {"Field": "Merchant", "Value": selected_case.get('merchant', 'N/A')},
                            {"Field": "Location", "Value": selected_case.get('location', 'N/A')},
                            {"Field": "Bank", "Value": selected_case.get('bank', 'N/A')},
                            {"Field": "Current Actual Fraud", "Value": selected_case.get('actual_fraud', 'Not set')},
                        ])
                        
                        st.dataframe(details_df, hide_index=True, use_container_width=True)
            else:
                st.warning("No cases found in database.")

        # --- Right Column: Validation Panel ---
        with col_right:
            if st.session_state.selected_case_id:
                selected_case = next((c for c in pending_cases if c["case_id"] == st.session_state.selected_case_id), None)
                
                if selected_case:
                    st.markdown("### Make a Decision")
                    
                    # Notes field
                    notes = st.text_area(
                        "📝 Validation Notes",
                        value=st.session_state.notes,
                        placeholder="Add your feedback or observations here...",
                        height=100,
                        key="validation_notes"
                    )
                    st.session_state.notes = notes
                    
                    st.markdown("#### Choose Action:")
                    
                    # Decision buttons
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
                    
                    st.divider()
                    
                    # Quick stats for this case
                    st.markdown("#### Case Insights")
                    risk_value = selected_case.get('risk_display', 'N/A')
                    if 'High' in str(risk_value):
                        st.warning("⚠️ High risk case - review carefully")
                    elif 'Medium' in str(risk_value):
                        st.info("ℹ️ Medium risk case")
                    else:
                        st.success("✅ Low risk case")
            else:
                # Empty state for right column when no case selected
                pass

        st.divider()

        # --- Fraud Cases Table ---
        st.subheader("📋 Fraud Cases")
        
        if not pending_cases:
            st.warning("No cases found in database.")
        else:
            # Create a DataFrame for display using actual database values
            display_data = []
            for case in pending_cases:
                display_data.append({
                    "Case ID": case.get('case_id', 'N/A'),  # Using actual case_id from database (e.g., FR-2025-4000)
                    "Date": case.get('transaction_date', 'N/A'),
                    "Amount": case.get('amount_formatted', 'N/A'),
                    "Risk": case.get('risk_display', 'N/A'),
                    "Merchant": case.get('merchant', 'N/A'),
                    "Location": case.get('location', 'N/A'),
                    "Bank": case.get('bank', 'N/A'),
                    "Actual Fraud": case.get('actual_fraud', 'Pending'),
                })
            
            df_display = pd.DataFrame(display_data)
            
            # Show the full table
            st.dataframe(
                df_display,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Case ID": st.column_config.TextColumn("Case ID", width="medium"),
                    "Date": st.column_config.DateColumn("Date", width="small"),
                    "Amount": st.column_config.TextColumn("Amount", width="small"),
                    "Risk": st.column_config.TextColumn("Risk", width="small"),
                    "Merchant": st.column_config.TextColumn("Merchant", width="medium"),
                    "Location": st.column_config.TextColumn("Location", width="medium"),
                    "Bank": st.column_config.TextColumn("Bank", width="small"),
                    "Actual Fraud": st.column_config.TextColumn("Actual Fraud", width="small"),
                }
            )
            
            # Show row count
            st.caption(f"Showing {len(pending_cases)} total cases")
            
            # Export button
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("📥 Export Table to CSV", use_container_width=True):
                    if cases:
                        export_df = pd.DataFrame(cases)
                        csv = export_df.to_csv(index=False)
                        st.download_button(
                            label="Download CSV",
                            data=csv,
                            file_name=f"fraud_cases_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv",
                            key="export_all_cases"
                        )

    render()