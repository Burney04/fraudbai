import streamlit as st
import pandas as pd
from FraudShield.utils.supabase_client import supabase
from datetime import datetime
import re

def show():
    # --- Optimized: Reduced data loading and better caching ---
    @st.cache_data(ttl=300, show_spinner=False)
    def load_fraud_cases():
        """Load fraud cases - dynamically fetch only unvalidated cases."""
        try:
            # First, get all validated case IDs
            validated_response = supabase.table("validated_cases") \
                .select("case_id") \
                .execute()
            
            validated_ids = set([item['case_id'] for item in validated_response.data]) if validated_response.data else set()
            
            # Load a larger set to ensure we can find 1000 unvalidated cases
            # We'll fetch 3000 and filter down to 1000 unvalidated
            response = supabase.table("fraud_cases") \
                .select("case_id, amount_formatted, risk_display, transaction_date, sentiment, fraud_terms, complaint_link, customer_history, actual_fraud") \
                .limit(3000) \
                .execute()
            
            if not response.data:
                return []
            
            df = pd.DataFrame(response.data)
            if 'case_id' in df.columns:
                df['case_id'] = df['case_id'].astype(str)
            
            # Filter out already validated cases
            if validated_ids:
                df = df[~df['case_id'].isin(validated_ids)]
            
            # Extract numeric part and sort properly (smallest IDs first)
            df['case_id_num'] = df['case_id'].str.extract(r'(\d+)$').astype(int)
            df = df.sort_values('case_id_num')
            
            # Take the first 1000 smallest case IDs that are unvalidated
            df = df.head(1000).drop('case_id_num', axis=1)
            
            return df.to_dict('records')
        except Exception as e:
            st.error(f"Error loading fraud cases: {e}")
            return []

    @st.cache_data(ttl=300, show_spinner=False)
    def load_validated_cases():
        """Load validated cases - limited and optimized with numeric sorting."""
        try:
            response = supabase.table("validated_cases") \
                .select("case_id, amount, risk_score, sentiment, fraud_terms, complaint_link, customer_history, validated, valid_type, feedback_notes, timestamp, updated_at") \
                .execute()
            
            if response.data:
                # ✅ FIXED: Sort by numeric case_id before returning
                data = response.data
                data.sort(key=lambda x: int(re.search(r'(\d+)$', x['case_id']).group(1)) if re.search(r'(\d+)$', x['case_id']) else 0)
                return data
            return []
        except Exception as e:
            st.error(f"Error loading validated cases: {e}")
            return []

    # --- Optimized: Pre-compile regex pattern ---
    RISK_PERCENTAGE_PATTERN = re.compile(r'(\d+)%')
    RISK_DECIMAL_PATTERN = re.compile(r'\((\d+\.?\d*)\)')
    
    @st.cache_data(ttl=3600)
    def extract_risk_score(risk_display):
        """Extract numeric risk score - cached for performance."""
        try:
            if not risk_display:
                return 0.5
            
            risk_str = str(risk_display)
            
            percentage_match = RISK_PERCENTAGE_PATTERN.search(risk_str)
            if percentage_match:
                return int(percentage_match.group(1)) / 100
            
            decimal_match = RISK_DECIMAL_PATTERN.search(risk_str)
            if decimal_match:
                return float(decimal_match.group(1))
            
            return 0.5
        except:
            return 0.5

    # --- Update validated case ---
    def update_validated_case(case_id, valid_type, feedback_notes, user_email):
        """Update an existing validated case."""
        try:
            update_data = {
                "valid_type": valid_type,
                "validated": user_email,
                "feedback_notes": feedback_notes,
                "updated_at": datetime.now().isoformat()
            }
            
            supabase.table("validated_cases") \
                .update(update_data) \
                .eq("case_id", case_id) \
                .execute()
            
            return True, f"Case {case_id} updated successfully"
        except Exception as e:
            return False, f"Error updating case: {e}"

    # --- Optimized: Batch validation check ---
    def get_validated_case_ids():
        """Get set of validated case IDs in one query."""
        try:
            response = supabase.table("validated_cases") \
                .select("case_id") \
                .execute()
            return {item['case_id'] for item in response.data} if response.data else set()
        except:
            return set()

    # --- Optimized: Batch insert for auto-validation ---
    def auto_validate_high_risk_cases(cases, user_email):
        """Auto-validate high-risk cases - optimized batch check."""
        validated_ids = get_validated_case_ids()
        
        validated_count = 0
        for case in cases:
            risk_score = extract_risk_score(case.get('risk_display', 'N/A'))
            case_id = case.get('case_id')
            
            if risk_score > 0.90 and case_id not in validated_ids:
                try:
                    risk_percentage = f"{int(risk_score * 100)}%"
                    insert_data = {
                        "case_id": case_id,
                        "amount": case.get('amount_formatted'),
                        "risk_score": risk_percentage,
                        "sentiment": case.get('sentiment'),
                        "fraud_terms": case.get('fraud_terms'),
                        "complaint_link": case.get('complaint_link'),
                        "customer_history": case.get('customer_history'),
                        "model_prediction": "N/A",
                        "validated": "Auto-Confirmed",
                        "valid_type": "Confirmed Fraud",
                        "shap": "N/A",
                        "key_reason": "N/A",
                        "feedback_notes": "Auto-validated due to high risk score (>90%)",
                        "timestamp": datetime.now().isoformat()
                    }
                    supabase.table("validated_cases").insert(insert_data).execute()
                    validated_count += 1
                except Exception:
                    pass
        
        if validated_count > 0:
            st.toast(f"🤖 Auto-validated {validated_count} high-risk case(s)", icon="🤖")
            st.cache_data.clear()
            st.rerun()

    # --- Optimized: Single database update ---
    def insert_validated_case(case_data, user_email, valid_type, feedback_notes):
        """Insert validated case - optimized."""
        try:
            risk_score = extract_risk_score(case_data.get('risk_display', 'N/A'))
            risk_percentage = f"{int(risk_score * 100)}%"
            
            insert_data = {
                "case_id": case_data.get('case_id'),
                "amount": case_data.get('amount_formatted'),
                "risk_score": risk_percentage,
                "sentiment": case_data.get('sentiment'),
                "fraud_terms": case_data.get('fraud_terms'),
                "complaint_link": case_data.get('complaint_link'),
                "customer_history": case_data.get('customer_history'),
                "model_prediction": "N/A",
                "validated": user_email if user_email else "Auto-Confirmed",
                "valid_type": valid_type,
                "shap": "N/A",
                "key_reason": "N/A",
                "feedback_notes": feedback_notes,
                "timestamp": datetime.now().isoformat()
            }
            
            supabase.table("validated_cases").insert(insert_data).execute()
            return True, f"Case {case_data.get('case_id')} added"
        except Exception as e:
            return False, f"Error: {e}"

    # Initialize session state
    def init_state():
        """Initialize session state with minimal variables."""
        defaults = {
            "cases": load_fraud_cases(),
            "validated_cases": load_validated_cases(),
            "selected_case_id": None,
            "selected_reval_case_id": None,
            "notes": "",
            "pending_page": 0,
            "validated_page": 0,
            "confirm_update": None
        }
        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value

    # --- Main handlers ---
    def handle_validate(case_id, decision, valid_type, feedback_notes):
        """Handle case validation."""
        try:
            supabase.table("fraud_cases") \
                .update({"actual_fraud": decision}) \
                .eq("case_id", case_id) \
                .execute()
        except Exception as e:
            st.error(f"Error updating database: {e}")
            return
        
        selected_case = next((c for c in st.session_state.cases if c["case_id"] == case_id), None)
        if selected_case:
            user_email = st.session_state.user.email if hasattr(st.session_state, 'user') else "Unknown"
            success, message = insert_validated_case(selected_case, user_email, valid_type, feedback_notes)
            
            if success:
                st.cache_data.clear()
                st.session_state.validated_cases = load_validated_cases()
                st.toast(f"✅ Case {case_id} {decision}", icon="✅")
            else:
                st.error(message)
        
        st.session_state.notes = ""
        st.session_state.selected_case_id = None
        st.rerun()

    def handle_revalidation(case_id, valid_type, feedback_notes):
        """Handle revalidation of an existing case."""
        user_email = st.session_state.user.email if hasattr(st.session_state, 'user') else "Unknown"
        success, message = update_validated_case(case_id, valid_type, feedback_notes, user_email)
        
        if success:
            st.cache_data.clear()
            st.session_state.validated_cases = load_validated_cases()
            st.toast(f"✅ Case {case_id} revalidated successfully", icon="✅")
            st.session_state.confirm_update = None
            st.session_state.selected_reval_case_id = None
            st.rerun()
        else:
            st.error(message)

    def refresh_data():
        """Refresh all data."""
        st.cache_data.clear()
        st.session_state.cases = load_fraud_cases()
        st.session_state.validated_cases = load_validated_cases()
        st.session_state.pending_page = 0
        st.session_state.validated_page = 0
        st.session_state.selected_case_id = None
        st.session_state.selected_reval_case_id = None
        st.rerun()

    # --- Render function ---
    def render():
        """Main UI - optimized rendering."""
        init_state()

        cases = st.session_state.cases
        validated_cases_list = st.session_state.validated_cases
        selected_case_id = st.session_state.selected_case_id
        notes = st.session_state.notes
        
        user_email = st.session_state.user.email if hasattr(st.session_state, 'user') else "Unknown"
        
        # Auto-validate on load
        auto_validate_high_risk_cases(cases, user_email)

        # --- Header ---
        st.title("🧾 Fraud Case Validation")
        # ✅ UPDATED: Clarified that this is a validation queue with sliding window behavior
        st.caption(f"📊 Validation queue: {len(cases)} pending cases (new cases appear as others are validated)")
        
        # Refresh button
        col_title, col_refresh = st.columns([6, 1])
        with col_refresh:
            if st.button("🔄 Refresh Data", use_container_width=True):
                refresh_data()

        st.divider()
        
        # --- Validation Summary Section ---
        st.subheader("📊 Validation Summary")
        
        validated_case_ids = [v['case_id'] for v in validated_cases_list]
        
        confirmed_cases = []
        pending_ambiguous_cases = []
        
        for case in cases:
            risk_score = extract_risk_score(case.get('risk_display', 'N/A'))
            is_validated = case['case_id'] in validated_case_ids
            
            if is_validated or risk_score > 0.90:
                confirmed_cases.append(case)
            else:
                pending_ambiguous_cases.append(case)
        
        confirmed_count = len([v for v in validated_cases_list if v.get('valid_type') == 'Confirmed Fraud'])
        legitimate_count = len([v for v in validated_cases_list if v.get('valid_type') == 'Legitimate'])
        escalated_count = len([v for v in validated_cases_list if v.get('valid_type') == 'Escalated'])
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("⏳ Pending Validation", len(pending_ambiguous_cases))
        with col2:
            st.metric("✅ Confirmed Fraud", confirmed_count)
        with col3:
            st.metric("🟢 Legitimate", legitimate_count)
        with col4:
            st.metric("🟣 Escalated", escalated_count)
        
        st.divider()
        
        # --- Tabs (Now with 2 tabs) ---
        tab1, tab2 = st.tabs(["⚠️ Pending Cases", "✅ Validated Cases"])
        
        # --- Tab 1: Pending Cases ---
        with tab1:
            validated_ids = set(validated_case_ids)
            pending_cases = [c for c in cases if c['case_id'] not in validated_ids and extract_risk_score(c.get('risk_display', 'N/A')) <= 0.90]
            st.caption(f"Cases needing validation: {len(pending_cases)}")
            
            if pending_cases:
                CARDS_PER_PAGE = 10
                total_pages = max(1, (len(pending_cases) + CARDS_PER_PAGE - 1) // CARDS_PER_PAGE)
                
                if st.session_state.pending_page >= total_pages:
                    st.session_state.pending_page = total_pages - 1
                
                start_idx = st.session_state.pending_page * CARDS_PER_PAGE
                current_cases = pending_cases[start_idx:start_idx + CARDS_PER_PAGE]
                
                col_left, col_right = st.columns([2, 1])
                
                with col_left:
                    st.markdown(f"**Page {st.session_state.pending_page + 1} / {total_pages}**")
                    
                    for idx, case in enumerate(current_cases):
                        risk_score = extract_risk_score(case.get('risk_display', 'N/A'))
                        risk_pct = int(risk_score * 100)
                        
                        if risk_pct >= 80:
                            badge_color = "#DC2626"
                            badge_bg = "#FEE2E2"
                        elif risk_pct >= 60:
                            badge_color = "#D97706"
                            badge_bg = "#FEF3C7"
                        else:
                            badge_color = "#059669"
                            badge_bg = "#D1FAE5"
                        
                        if selected_case_id == case["case_id"]:
                            border_style = "2px solid #3B82F6"
                            bg_color = "rgba(59, 130, 246, 0.1)"
                        else:
                            border_style = "1px solid rgba(128, 128, 128, 0.2)"
                            bg_color = "transparent"
                        
                        st.markdown(f"""
                        <div style='border:{border_style}; border-radius:12px; padding:12px; margin-bottom:10px; background:{bg_color};'>
                            <div style='display:flex; justify-content:space-between; margin-bottom:8px;'>
                                <strong>📌 {case['case_id']}</strong>
                                <span style='background:{badge_bg}; color:{badge_color}; padding:2px 8px; border-radius:12px; font-size:12px;'>
                                    {risk_pct}% Risk
                                </span>
                            </div>
                            <div>💰 {case.get('amount_formatted', 'N/A')}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if st.button(f"Select", key=f"select_{case['case_id']}_{idx}", use_container_width=True):
                            st.session_state.selected_case_id = case["case_id"]
                            st.rerun()
                    
                    if total_pages > 1:
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("◀ Previous", disabled=(st.session_state.pending_page == 0), use_container_width=True):
                                st.session_state.pending_page -= 1
                                st.rerun()
                        with col2:
                            if st.button("Next ▶", disabled=(st.session_state.pending_page >= total_pages - 1), use_container_width=True):
                                st.session_state.pending_page += 1
                                st.rerun()
                
                with col_right:
                    with st.container(border=True):
                        st.markdown("### 🧩 Validation Decision")
                        
                        selected_case = next((c for c in pending_cases if c["case_id"] == selected_case_id), None)
                        
                        if selected_case:
                            risk_score = extract_risk_score(selected_case.get('risk_display', 'N/A'))
                            risk_pct = int(risk_score * 100)
                            
                            st.markdown(f"**Case:** `{selected_case['case_id']}`")
                            st.markdown(f"**💰 Amount:** {selected_case.get('amount_formatted', 'N/A')}")
                            st.markdown(f"**📊 Risk Score:** {risk_pct}%")
                            st.markdown(f"**📅 Date:** {selected_case.get('transaction_date', 'N/A')}")
                            
                            st.markdown("---")
                            
                            notes = st.text_area("💬 Feedback Notes", value=st.session_state.notes, placeholder="Add feedback...", height=80, key="validation_notes")
                            st.session_state.notes = notes
                            
                            st.markdown("---")
                            
                            col_a, col_b, col_c = st.columns(3)
                            with col_a:
                                if st.button("✅ Confirm Fraud", use_container_width=True, type="primary"):
                                    handle_validate(selected_case["case_id"], "confirmed", "Confirmed Fraud", notes)
                            with col_b:
                                if st.button("🟢 Legitimate", use_container_width=True):
                                    handle_validate(selected_case["case_id"], "rejected", "Legitimate", notes)
                            with col_c:
                                if st.button("🟣 Escalate", use_container_width=True):
                                    handle_validate(selected_case["case_id"], "escalated", "Escalated", notes)
                            
                            if st.button("🔍 Inspect Case", use_container_width=True):
                                st.session_state.selected_case_id = selected_case["case_id"]
                                st.query_params["page"] = "Drill-Down Inspection"
                                st.query_params["case_id"] = selected_case["case_id"]
                                st.rerun()
                        else:
                            st.info("👈 Select a case")
            else:
                st.success("✅ No pending cases!")
        
        # --- Tab 2: Validated Cases with Conditional Display ---
        with tab2:
            # Check if a case is selected for revalidation
            if st.session_state.selected_reval_case_id:
                # --- Revalidate Cases Section (shown when a case is selected) ---
                selected_case = next((v for v in validated_cases_list if v["case_id"] == st.session_state.selected_reval_case_id), None)
                
                if selected_case:
                    st.markdown(f"### 🔄 Revalidate Case: `{selected_case['case_id']}`")
                    
                    # Back button to return to table view
                    if st.button("← Back to Validated Cases", use_container_width=True):
                        st.session_state.selected_reval_case_id = None
                        st.rerun()
                    
                    st.markdown("---")
                    
                    # Display case information
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**💰 Amount:** {selected_case.get('amount', 'N/A')}")
                        st.markdown(f"**📅 Transaction Date:** {selected_case.get('transaction_date', 'N/A')}")
                    with col2:
                        st.markdown(f"**📊 Risk Score:** {selected_case.get('risk_score', 'N/A')}")
                        complaint_link = selected_case.get('complaint_link', 'N/A')
                        if complaint_link and str(complaint_link).strip() and complaint_link != 'N/A':
                            st.markdown(f"**🔗 Complaint Link:** ✅ Linked")
                        else:
                            st.markdown(f"**🔗 Complaint Link:** ❌ No link")
                    
                    st.markdown("---")
                    
                    # Current validation info
                    st.markdown("#### Current Validation Information")
                    col_curr1, col_curr2, col_curr3 = st.columns(3)
                    with col_curr1:
                        st.markdown(f"**Validated By:** {selected_case.get('validated', 'N/A')}")
                    with col_curr2:
                        st.markdown(f"**Valid Type:** {selected_case.get('valid_type', 'N/A')}")
                    with col_curr3:
                        updated_at = selected_case.get('updated_at', selected_case.get('timestamp', 'N/A'))
                        st.markdown(f"**Last Updated:** {updated_at[:10] if updated_at else 'N/A'}")
                    
                    st.markdown(f"**Current Feedback Notes:**")
                    st.info(selected_case.get('feedback_notes', 'No feedback notes provided.'))
                    
                    st.markdown("---")
                    
                    # Update form
                    updated_notes = st.text_area(
                        "📝 Updated Feedback Notes",
                        value=selected_case.get('feedback_notes', ''),
                        placeholder="Add your updated feedback or observations here...",
                        height=100,
                        key="revalidation_notes"
                    )
                    
                    st.markdown("**Select New Action:**")
                    col_update_a, col_update_b, col_update_c = st.columns(3)
                    
                    with col_update_a:
                        if st.button("✅ Revalidate as Confirmed Fraud", use_container_width=True, type="primary", key="reval_confirmed"):
                            st.session_state.confirm_update = {
                                "case_id": selected_case['case_id'],
                                "valid_type": "Confirmed Fraud",
                                "notes": updated_notes
                            }
                            st.rerun()
                    
                    with col_update_b:
                        if st.button("🟢 Revalidate as Legitimate", use_container_width=True, key="reval_legitimate"):
                            st.session_state.confirm_update = {
                                "case_id": selected_case['case_id'],
                                "valid_type": "Legitimate",
                                "notes": updated_notes
                            }
                            st.rerun()
                    
                    with col_update_c:
                        if st.button("🟣 Revalidate as Escalated", use_container_width=True, key="reval_escalated"):
                            st.session_state.confirm_update = {
                                "case_id": selected_case['case_id'],
                                "valid_type": "Escalated",
                                "notes": updated_notes
                            }
                            st.rerun()
                    
                    # Confirmation dialog
                    if st.session_state.confirm_update:
                        case_id = st.session_state.confirm_update["case_id"]
                        valid_type = st.session_state.confirm_update["valid_type"]
                        notes = st.session_state.confirm_update["notes"]
                        
                        st.warning(f"⚠️ Are you sure you want to revalidate Case {case_id} to '{valid_type}' as {user_email}?")
                        st.caption("This will update the validation record and cannot be undone.")
                        
                        col_confirm1, col_confirm2 = st.columns(2)
                        with col_confirm1:
                            if st.button("✅ Yes, Revalidate Case", use_container_width=True):
                                handle_revalidation(case_id, valid_type, notes)
                                st.session_state.confirm_update = None
                                st.rerun()
                        with col_confirm2:
                            if st.button("❌ No, Cancel", use_container_width=True):
                                st.session_state.confirm_update = None
                                st.session_state.selected_reval_case_id = None
                                st.rerun()
                else:
                    st.info("Selected case not found.")
                    st.session_state.selected_reval_case_id = None
                    st.rerun()
            
            else:
                # --- Validated Cases Table (shown when no case is selected) ---
                st.caption(f"Validated cases: {len(validated_cases_list)}")
                
                if validated_cases_list:
                    # Pagination for validated cases
                    ROWS_PER_PAGE = 10
                    total_pages = max(1, (len(validated_cases_list) + ROWS_PER_PAGE - 1) // ROWS_PER_PAGE)
                    
                    if st.session_state.validated_page >= total_pages:
                        st.session_state.validated_page = total_pages - 1
                    if st.session_state.validated_page < 0:
                        st.session_state.validated_page = 0
                    
                    start_idx = st.session_state.validated_page * ROWS_PER_PAGE
                    end_idx = min(start_idx + ROWS_PER_PAGE, len(validated_cases_list))
                    current_validated_cases = validated_cases_list[start_idx:end_idx]
                    
                    st.markdown(f"**Page {st.session_state.validated_page + 1} / {total_pages}** (Showing {start_idx + 1}-{end_idx} of {len(validated_cases_list)} cases)")
                    
                    # ✅ FIXED: Sort by numeric case_id, not alphabetical string sorting
                    # Extract numeric part and sort properly (smallest IDs first)
                    all_case_ids = sorted(
                        [v['case_id'] for v in validated_cases_list],
                        key=lambda x: int(re.search(r'(\d+)$', x).group(1)) if re.search(r'(\d+)$', x) else 0
                    )
                    
                    selected_revalidation = st.selectbox(
                        "Select a validated case to revalidate:",
                        options=all_case_ids,
                        index=None,
                        placeholder="Type or select a case...",
                        key="revalidation_select"
                    )
                    
                    if selected_revalidation:
                        st.session_state.selected_reval_case_id = selected_revalidation
                        st.rerun()
                    
                    # Display the table with Revalidate button (still paginated for performance)
                    st.markdown("### Validated Cases")
                    
                    # Create DataFrame for display
                    display_data = []
                    for case in current_validated_cases:
                        display_data.append({
                            "Case ID": case.get('case_id', 'N/A'),
                            "Valid Type": case.get('valid_type', 'N/A'),
                            "Validated By": case.get('validated', 'N/A'),
                            "Date": case.get('timestamp', 'N/A')[:10] if case.get('timestamp') else 'N/A',
                            "Action": "Revalidate"
                        })
                    
                    df_display = pd.DataFrame(display_data)
                    
                    # Display the table
                    for idx, row in df_display.iterrows():
                        col1, col2, col3, col4, col5 = st.columns([2, 1.5, 1.5, 1.5, 1])
                        with col1:
                            st.write(row['Case ID'])
                        with col2:
                            st.write(row['Valid Type'])
                        with col3:
                            st.write(row['Validated By'])
                        with col4:
                            st.write(row['Date'])
                        with col5:
                            if st.button(f"Revalidate", key=f"revalidate_{row['Case ID']}_{idx}", use_container_width=True):
                                st.session_state.selected_reval_case_id = row['Case ID']
                                st.rerun()
                        st.divider()
                    
                    # Pagination controls
                    if total_pages > 1:
                        col_prev, col_next = st.columns(2)
                        with col_prev:
                            if st.button("◀ Previous", disabled=(st.session_state.validated_page == 0), use_container_width=True, key="validated_prev"):
                                st.session_state.validated_page -= 1
                                st.rerun()
                        with col_next:
                            if st.button("Next ▶", disabled=(st.session_state.validated_page >= total_pages - 1), use_container_width=True, key="validated_next"):
                                st.session_state.validated_page += 1
                                st.rerun()
                    
                    # Export button
                    st.markdown("---")
                    if st.button("📥 Export Full List", use_container_width=True):
                        export_data = [{
                            "Case ID": v.get('case_id', 'N/A'),
                            "Amount": v.get('amount', 'N/A'),
                            "Risk Score": v.get('risk_score', 'N/A'),
                            "Valid Type": v.get('valid_type', 'N/A'),
                            "Validated By": v.get('validated', 'N/A'),
                            "Feedback Notes": v.get('feedback_notes', 'N/A')
                        } for v in validated_cases_list]
                        export_df = pd.DataFrame(export_data)
                        csv = export_df.to_csv(index=False)
                        st.download_button("Download CSV", data=csv, file_name=f"validated_cases_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")
                else:
                    st.info("No validated cases yet")
    
    render()