import streamlit as st
import pandas as pd
import numpy as np
import re
from FraudShield.utils.supabase_client import supabase
from datetime import datetime

def show():
    # --------------------------
    # PAGE HEADER
    # --------------------------
    st.title("Drill-Down Case Inspection")
    st.markdown("**Inspect and analyze fraud case with more details**")

    # --------------------------
    # HELPER FUNCTIONS (Enhanced for better risk extraction)
    # --------------------------
    def extract_risk_score(risk_display):
        """
        Convert risk display to numeric score.
        Supports formats:
        - "High (0.85)" -> 0.85
        - "57% - Medium" -> 0.57
        - "85%" -> 0.85
        - "High Risk - 92%" -> 0.92
        - "Medium (45%)" -> 0.45
        """
        try:
            if pd.isna(risk_display):
                return 0.5
            
            risk_str = str(risk_display)
            
            # Try to find percentage format (e.g., "57%", "85%")
            percentage_match = re.search(r'(\d+)%', risk_str)
            if percentage_match:
                return int(percentage_match.group(1)) / 100
            
            # Try to find decimal in parentheses (e.g., "High (0.85)")
            decimal_match = re.search(r'\((\d+\.?\d*)\)', risk_str)
            if decimal_match:
                return float(decimal_match.group(1))
            
            # Try to find any decimal number
            decimal_match2 = re.search(r'(\d+\.\d+)', risk_str)
            if decimal_match2:
                return float(decimal_match2.group(1))
            
            # Fallback based on text
            risk_lower = risk_str.lower()
            if 'high' in risk_lower:
                return 0.85
            elif 'medium' in risk_lower:
                return 0.45
            elif 'low' in risk_lower:
                return 0.15
            else:
                return 0.5
                
        except Exception as e:
            print(f"Error extracting risk score: {e}")
            return 0.5

    def extract_amount(amount_formatted):
        """Convert formatted amount like 'RM 8,500' to float."""
        try:
            if pd.isna(amount_formatted):
                return 0.0
            # Remove currency symbols and commas, convert to float
            amount_str = str(amount_formatted).replace('RM', '').replace('MYR', '').replace('$', '').replace(',', '').strip()
            return float(amount_str)
        except:
            return 0.0

    def get_risk_level(risk_display):
        """Get risk level category from risk display."""
        try:
            if pd.isna(risk_display):
                return 'Unknown'
            risk_str = str(risk_display).lower()
            if 'high' in risk_str:
                return 'High'
            elif 'medium' in risk_str:
                return 'Medium'
            elif 'low' in risk_str:
                return 'Low'
            else:
                # Try to determine from percentage
                percentage_match = re.search(r'(\d+)%', risk_str)
                if percentage_match:
                    score = int(percentage_match.group(1))
                    if score >= 70:
                        return 'High'
                    elif score >= 40:
                        return 'Medium'
                    else:
                        return 'Low'
                return 'Unknown'
        except:
            return 'Unknown'
    
    def get_risk_percentage_display(risk_score):
        """Convert numeric score to percentage display."""
        return f"{int(risk_score * 100)}%"

    # --------------------------
    # LOAD DATA FROM SUPABASE (LIMITED TO 1000 ROWS)
    # --------------------------
    @st.cache_data(ttl=300, max_entries=1)
    def load_fraud_cases():
        """Load first 1000 fraud cases from Supabase."""
        try:
            # Load only first 1000 records
            response = supabase.table("fraud_cases") \
                .select("*") \
                .limit(1000) \
                .execute()
            
            if response.data:
                df = pd.DataFrame(response.data)
                total_loaded = len(df)
                
                # Process the data
                if 'transaction_date' in df.columns:
                    df['transaction_date'] = pd.to_datetime(df['transaction_date'])
                    df['date'] = df['transaction_date'].dt.date
                    df['date_str'] = df['transaction_date'].dt.strftime('%Y-%m-%d')
                    df['time'] = df['transaction_date'].dt.strftime('%H:%M:%S')
                
                # Extract numeric values for filtering and calculations
                df['risk_score_numeric'] = df['risk_display'].apply(extract_risk_score)
                df['risk_percentage'] = df['risk_score_numeric'].apply(lambda x: f"{int(x*100)}%")
                df['amount_numeric'] = df['amount_formatted'].apply(extract_amount)
                df['risk_level'] = df['risk_display'].apply(get_risk_level)
                
                return df, total_loaded, None
            else:
                return get_sample_data(), 0, "No data found in the database"
                
        except Exception as e:
            error_msg = f"Error loading data from Supabase: {str(e)}"
            return get_sample_data(), 0, error_msg
    
    def get_sample_data():
        """Return sample data if Supabase is unavailable."""
        # Create sample data (limited to 1000 for sample)
        np.random.seed(42)
        n_samples = 1000
        
        # Create risk displays in various formats to test extraction
        risk_formats = [
            "High (0.85)", "Medium (0.45)", "Low (0.15)",
            "85% - High", "57% - Medium", "23% - Low",
            "High Risk - 92%", "Medium Risk - 48%", "Low Risk - 12%"
        ]
        
        sample_data = {
            'case_id': [f'FR-2025-{i:04d}' for i in range(1000, 1000+n_samples)],
            'transaction_date': pd.date_range(start='2023-01-01', periods=n_samples, freq='h')[:n_samples],
            'amount_formatted': [f"RM {np.random.uniform(10, 50000):,.2f}" for _ in range(n_samples)],
            'risk_display': np.random.choice(risk_formats, n_samples),
            'merchant': np.random.choice(['TechMart', 'Shopee', 'Lazada', 'Amazon', 'Grab'], n_samples),
            'location': np.random.choice(['Kuala Lumpur', 'Penang', 'Johor Bahru', 'Selangor', 'Sabah'], n_samples),
            'card_number': [f"**** **** **** {np.random.randint(1000, 9999)}" for _ in range(n_samples)],
            'bank': np.random.choice(['Maybank', 'CIMB', 'Public Bank', 'RHB', 'Hong Leong'], n_samples),
            'complaint_text': [
                "Customer reported unauthorized transaction. Suspicious activity detected.",
                "Transaction occurred at unusual time with immediate action needed.",
                "Multiple failed attempts before successful transaction.",
                "Merchant flagged as high-risk in previous cases.",
                "Customer claims card was not present during transaction."
            ] * (n_samples // 5 + 1),
        }
        
        df = pd.DataFrame(sample_data)
        
        # Process the data
        df['transaction_date'] = pd.to_datetime(df['transaction_date'])
        df['date'] = df['transaction_date'].dt.date
        df['date_str'] = df['transaction_date'].dt.strftime('%Y-%m-%d')
        df['time'] = df['transaction_date'].dt.strftime('%H:%M:%S')
        df['risk_score_numeric'] = df['risk_display'].apply(extract_risk_score)
        df['risk_percentage'] = df['risk_score_numeric'].apply(lambda x: f"{int(x*100)}%")
        df['amount_numeric'] = df['amount_formatted'].apply(extract_amount)
        df['risk_level'] = df['risk_display'].apply(get_risk_level)
        
        return df

    # --------------------------
    # LOAD DATA
    # --------------------------
    with st.spinner("Loading fraud case data..."):
        df, total_loaded, error = load_fraud_cases()
    
    if error:
        st.error(error)
        st.info("Using sample data for demonstration.")
    
    # --------------------------
    # CASE SELECTION
    # --------------------------
    st.subheader("Case Selection")
    
    # Get selected case from session state (if coming from filter cases)
    # Convert to Python int to avoid numpy int64 issues
    default_index = 0
    if 'selected_case_id' in st.session_state and st.session_state.selected_case_id:
        # Find the index of the selected case
        matching_indices = df[df['case_id'] == st.session_state.selected_case_id].index.tolist()
        if matching_indices:
            # Convert numpy int64 to Python int
            default_index = int(matching_indices[0])
        else:
            st.warning(f"Case {st.session_state.selected_case_id} not found. Showing first case.")
            default_index = 0
    
    # Create selectbox with all case IDs
    case_options = df['case_id'].tolist()
    selected_case_id = st.selectbox(
        "Type or Select a case to inspect",
        options=case_options,
        index=default_index,  # Now this is a regular Python int
        key="case_inspect_select"
    )
    
    # Get the selected case data
    selected_case = df[df['case_id'] == selected_case_id].iloc[0]
    
    st.divider()
    
    # --------------------------
    # DISPLAY SELECTED CASE
    # --------------------------
    
    # Extract risk information (now using the enhanced extraction)
    risk_score = selected_case.get('risk_score_numeric', 0.5)
    risk_percentage = selected_case.get('risk_percentage', f"{int(risk_score*100)}%")
    risk_level = selected_case.get('risk_level', 'Unknown')
    original_risk_display = selected_case.get('risk_display', 'N/A')
    
    # Determine risk color and badge
    if risk_level == 'High':
        risk_color = "red"
        risk_badge = "🔴 High Risk"
        risk_emoji = "🟥"
    elif risk_level == 'Medium':
        risk_color = "orange"
        risk_badge = "🟠 Medium Risk"
        risk_emoji = "🟠"
    else:
        risk_color = "green"
        risk_badge = "🟢 Low Risk"
        risk_emoji = "🟢"
    
    # --------------------------
    # CASE OVERVIEW
    # --------------------------
    with st.container():
        st.markdown("### 🚨 Case Overview")
        
        # Header with Case ID and Risk
        col_title1, col_title2 = st.columns([2, 1])
        with col_title1:
            st.markdown(f"**Case ID:** {selected_case.get('case_id', 'N/A')}")
        with col_title2:
            st.markdown(f"**Risk Score:** **{risk_percentage}** ({risk_badge})")
        
        # Date and Time
        if 'date_str' in selected_case:
            st.markdown(f"**Date:** {selected_case['date_str']}")
        
        # Key information in columns
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write("**🏦 Bank:**", selected_case.get('bank', 'N/A'))
            st.write("**🛒 Merchant:**", selected_case.get('merchant', 'N/A'))
        with col2:
            st.write("**📍 Location:**", selected_case.get('location', 'N/A'))
            st.write("**🕓 Transaction Time:**", selected_case.get('time', 'N/A'))
        with col3:
            st.write("**💰 Amount:**", selected_case.get('amount_formatted', 'N/A'))
    
    st.divider()
    
    # --------------------------
    # STRUCTURED FEATURES
    # --------------------------
    st.subheader("📋 Structured Features")
    
    # Create structured features from available data
    structured_features = []
    
    # Transaction Amount
    structured_features.append({
        "label": "Transaction Amount",
        "value": selected_case.get('amount_formatted', 'N/A'),
        "risk": "N/A"
    })
    
    # Risk Score (with percentage)
    structured_features.append({
        "label": "Risk Score",
        "value": f"{risk_percentage} ({risk_level} Risk)",
        "risk": "N/A"
    })
    
    # Time of Day (if available)
    if 'time' in selected_case:
        hour = int(selected_case['time'].split(':')[0])
        if hour < 6 or hour > 22:
            time_risk = "high"
            time_desc = f"{selected_case['time']} (Off-hours)"
        else:
            time_risk = "low"
            time_desc = f"{selected_case['time']} (Business hours)"
        structured_features.append({
            "label": "Time of Day",
            "value": time_desc,
            "risk": "N/A"
        })
    
    # Transaction Date (if available)
    if 'date_str' in selected_case:
        structured_features.append({
            "label": "Transaction Date",
            "value": selected_case['date_str'],
            "risk": "N/A"
        })
    
    # Merchant (if available)
    if 'merchant' in selected_case:
        merchant_risk = "medium" if "electronics" in str(selected_case['merchant']).lower() or "high-value" in str(selected_case['merchant']).lower() else "low"
        structured_features.append({
            "label": "Merchant Category",
            "value": selected_case['merchant'],
            "risk": merchant_risk
        })
    
    # Display features in grid
    cols = st.columns(3)
    for i, feature in enumerate(structured_features):
        col = cols[i % 3]
        with col:
            color = "red" if feature["risk"] == "high" else "orange" if feature["risk"] == "medium" else "green"
            st.markdown(
                f"<div style='border:1px solid #ddd;padding:10px;border-radius:8px;"
                f"background-color:{color}10;margin-bottom:10px;'>"
                f"<b>{feature['label']}</b><br>"
                f"{feature['value']}<br>"
                f"<span style='color:{color};font-weight:bold;text-transform:capitalize;'>"
                f"{feature['risk']}</span></div>",
                unsafe_allow_html=True,
            )
    
    st.divider()
    
    # --------------------------
    # NLP ANALYSIS (Complaint Text)
    # --------------------------
    st.subheader("🧠 NLP Analysis")
    st.write("Extracted insights from complaint text:")
    
    if 'complaint_text' in selected_case and pd.notna(selected_case['complaint_text']):
        complaint_text = selected_case['complaint_text']
        st.info(complaint_text[:500] + ("..." if len(str(complaint_text)) > 500 else ""))
        
        # Basic NLP-like insights (simplified)
        st.markdown("**Key Insights:**")
        insights = []
        
        # Check for common fraud indicators
        complaint_lower = str(complaint_text).lower()
        if "unauthorized" in complaint_lower:
            insights.append("⚠️ Unauthorized transaction reported")
        if "scam" in complaint_lower or "fraud" in complaint_lower:
            insights.append("🚨 Fraud-related keywords detected")
        if "urgent" in complaint_lower or "immediate" in complaint_lower:
            insights.append("⏰ Urgency language detected - potential pressure tactic")
        if "sms" in complaint_lower or "message" in complaint_lower:
            insights.append("📱 Communication channel mentioned")
        
        if insights:
            for insight in insights:
                st.write(f"- {insight}")
        else:
            st.write("- No specific fraud indicators detected in complaint text")
    else:
        st.info("No complaint text available for this case.")
    
    st.divider()
    
    # --------------------------
    # SHAP EXPLAINABILITY
    # --------------------------
    st.subheader("📊 Model Explainability (SHAP)")
    st.write(f"Model explainability for **{selected_case_id}**")
    
    # Create a progress bar for risk score (using percentage)
    st.markdown(f"**Risk Score: {risk_percentage}**")
    st.progress(risk_score)
    
    # Simple feature importance visualization
    st.markdown("**Top contributing factors:**")
    st.write(f"**Will be implemented soon**: N/A")
    
    st.divider()
    
    # --------------------------
    # ACTION BUTTONS
    # --------------------------
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("📄 Export Report", use_container_width=True):
            # Create export data
            export_data = {
                "Case ID": selected_case_id,
                "Date": selected_case.get('date_str', 'N/A'),
                "Time": selected_case.get('time', 'N/A'),
                "Amount": selected_case.get('amount_formatted', 'N/A'),
                "Risk Score": risk_percentage,
                "Risk Level": risk_level,
                "Original Risk Value": original_risk_display,
                "Merchant": selected_case.get('merchant', 'N/A'),
                "Location": selected_case.get('location', 'N/A'),
                "Bank": selected_case.get('bank', 'N/A'),
                "Card Number": selected_case.get('card_number', 'N/A'),
            }
            export_df = pd.DataFrame([export_data])
            csv = export_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"case_{selected_case_id}_export.csv",
                mime="text/csv",
                key=f"export_{selected_case_id}"  # Add unique key to avoid conflicts
            )
    
    with col2:
        if st.button("🚀 Send to Validation Queue", use_container_width=True):
            # Store in session state and redirect
            st.session_state.selected_case_id = selected_case_id
            st.session_state.page = "Case_Validation"
            st.success(f"Case {selected_case_id} sent to validation queue ✅")
            st.rerun()
    
    with col3:
        if st.button("🔙 Back to Filter Cases", use_container_width=True):
            st.session_state.page = "filter_cases"
            st.rerun()