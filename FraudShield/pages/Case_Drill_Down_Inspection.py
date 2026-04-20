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
    # LOAD DATA FROM SUPABASE (FIXED: Ordered and includes case 4000)
    # --------------------------
    @st.cache_data(ttl=300, max_entries=1)
    def load_fraud_cases():
        """Load fraud cases from Supabase with consistent ordering starting from case 4000."""
        try:
            # ✅ FIXED: Order by case_id ascending and use gte to ensure case 4000+ are included
            # This ensures we always get cases starting from 4000 in ascending order
            response = supabase.table("fraud_cases") \
                .select("*") \
                .gte('case_id', 'FR-2025-4000') \
                .order('case_id', desc=False) \
                .limit(2000) \
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
                
                # Sort by numeric case_id to ensure correct order
                df['case_id_num'] = df['case_id'].str.extract(r'(\d+)$').astype(int)
                df = df.sort_values('case_id_num').drop('case_id_num', axis=1)
                
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
            'sentiment': np.random.choice(['Positive', 'Neutral', 'Negative'], n_samples),
            'fraud_terms': np.random.choice(['scam', 'fraud', 'unauthorized', 'chargeback', 'dispute'], n_samples),
            'complaint_link': np.random.choice(['https://example.com/complaint1', 'https://example.com/complaint2', ''], n_samples),
            'customer_history': np.random.choice(['New', 'Existing', 'VIP'], n_samples),
            'actual_fraud': np.random.choice(['confirmed', 'rejected', ''], n_samples, p=[0.15, 0.7, 0.15]),
            'card_number': [f"**** **** **** {np.random.randint(1000, 9999)}" for _ in range(n_samples)],
            'bank': np.random.choice(['Maybank', 'CIMB', 'Public Bank', 'RHB', 'Hong Leong'], n_samples),
            'merchant': np.random.choice(['TechMart', 'Shopee', 'Lazada', 'Amazon', 'Grab'], n_samples),
            'location': np.random.choice(['Kuala Lumpur', 'Penang', 'Johor Bahru', 'Selangor', 'Sabah'], n_samples),
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

    # --- Load validated cases for additional info ---
    @st.cache_data(ttl=300)
    def load_validated_case_info(case_id):
        """Load validation info from validated_cases table."""
        try:
            response = supabase.table("validated_cases") \
                .select("valid_type, validated") \
                .eq("case_id", case_id) \
                .execute()
            
            if response.data:
                return response.data[0]
            return None
        except:
            return None

    # --------------------------
    # LOAD DATA
    # --------------------------
    with st.spinner("Loading fraud case data..."):
        df, total_loaded, error = load_fraud_cases()
    
    if error:
        st.error(error)
        st.info("Using sample data for demonstration.")
    
    st.divider()
    
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
        index=default_index,
        key="case_inspect_select"
    )
    
    # Get the selected case data
    selected_case = df[df['case_id'] == selected_case_id].iloc[0]
    
    # Load validation info from validated_cases table
    validation_info = load_validated_case_info(selected_case_id)
    
    # --------------------------
    # DISPLAY SELECTED CASE
    # --------------------------
    
    # Extract risk information
    risk_score = selected_case.get('risk_score_numeric', 0.5)
    risk_percentage = selected_case.get('risk_percentage', f"{int(risk_score*100)}%")
    risk_level = selected_case.get('risk_level', 'Unknown')
    original_risk_display = selected_case.get('risk_display', 'N/A')
    
    # Determine risk badge (without emoji)
    if risk_level == 'High':
        risk_badge = "High Risk"
        risk_class = "risk-high"
    elif risk_level == 'Medium':
        risk_badge = "Medium Risk"
        risk_class = "risk-medium"
    else:
        risk_badge = "Low Risk"
        risk_class = "risk-low"
    
    # Determine Fraud Status (only show for risk score > 90%)
    if risk_score > 0.90:
        actual_fraud = selected_case.get('actual_fraud', 'N/A')
        if actual_fraud == 'confirmed':
            fraud_status = "✅ Confirmed Fraud"
        elif actual_fraud == 'rejected':
            fraud_status = "🟢 Legitimate"
        elif actual_fraud == 'escalated':
            fraud_status = "🟣 Escalated"
        else:
            fraud_status = "⏳ Pending Validation"
    else:
        fraud_status = "N/A"
    
    # --------------------------
    # TABS FOR CASE DETAILS WITH SPACING
    # --------------------------
    # Add custom CSS to increase tab spacing
    st.markdown(
        """
        <style>
        /* Increase spacing between tabs */
        button[data-baseweb="tab"] {
            margin-right: 110px !important;
            margin-left: 110px !important;
            padding-left: 15px !important;
            padding-right: 15px !important;
        }
        
        /* Adjust the tab container to center the tabs with spacing */
        div[data-baseweb="tab-list"] {
            gap: 30px !important;
            justify-content: center !important;
        }
        
        /* Optional: Add a subtle separator between tabs */
        button[data-baseweb="tab"]:not(:last-child)::after {
            content: "|";
            position: absolute;
            right: -20px;
            color: #E5E7EB;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Case Overview", 
        "📊 Features", 
        "🧠 NLP Analysis", 
        "📈 Model Explainability (SHAP)"
    ])
    
        # --------------------------
    # TAB 1: CASE OVERVIEW
    # --------------------------
    with tab1:
        # CSS styling for overview - only risk badge styling
        st.markdown(
            """
            <style>
            /* Risk badge styling */
            .risk-badge {
                display: inline-block;
                padding: 6px 14px !important;
                border-radius: 24px !important;
                font-size: 1rem !important;
                font-weight: 600 !important;
            }
            .risk-high { background-color: #FEE2E2; color: #DC2626; }
            .risk-medium { background-color: #FEF3C7; color: #D97706; }
            .risk-low { background-color: #D1FAE5; color: #059669; }
            
            /* Dark mode adjustments for risk badges */
            @media (prefers-color-scheme: dark) {
                .risk-high { background-color: #7F1D1D; color: #FCA5A5; }
                .risk-medium { background-color: #78350F; color: #FCD34D; }
                .risk-low { background-color: #064E3B; color: #6EE7B7; }
            }
            </style>
            """,
            unsafe_allow_html=True
        )
        
        # Row 1: Case ID and Date
        col1, col2 = st.columns(2)
        with col1:
            st.caption("📌 Case ID")
            st.markdown(f"### {selected_case.get('case_id', 'N/A')}")
        with col2:
            st.caption("📅 Date")
            st.markdown(f"### {selected_case.get('date_str', 'N/A')}")
        
        # Row 2: Risk Score and Amount
        col3, col4 = st.columns(2)
        with col3:
            st.caption("🎯 Risk Score")
            st.markdown(
                f'<span class="risk-badge {risk_class}">{risk_percentage} ({risk_badge})</span>',
                unsafe_allow_html=True
            )
        with col4:
            st.caption("💰 Amount")
            st.markdown(f"### {selected_case.get('amount_formatted', 'N/A')}")
    
    # --------------------------
    # TAB 2: FEATURES (Structured & Unstructured)
    # --------------------------
    with tab2:
        # ----- STRUCTURED FEATURES -----
        st.subheader("📊 Structured Features")
        
        structured_features = []
        
        # Transaction Amount
        structured_features.append({
            "label": "Transaction Amount",
            "value": selected_case.get('amount_formatted', 'N/A')
        })
        
        # Risk Score
        structured_features.append({
            "label": "Risk Score",
            "value": f"{risk_percentage} ({risk_level} Risk)"
        })
        
        # Transaction Date
        if 'date_str' in selected_case:
            structured_features.append({
                "label": "Transaction Date",
                "value": selected_case['date_str']
            })
        
        # Customer History (replacing Sentiment)
        if 'customer_history' in selected_case:
            customer_history = selected_case.get('customer_history', 'N/A')
            structured_features.append({
                "label": "Customer History",
                "value": customer_history
            })
        
        # Valid Type (from validated_cases table)
        valid_type_value = validation_info.get('valid_type', 'N/A') if validation_info else 'N/A'
        structured_features.append({
            "label": "Valid Type",
            "value": valid_type_value
        })
        
        # Validated By (from validated_cases table)
        validated_by_value = validation_info.get('validated', 'N/A') if validation_info else 'N/A'
        structured_features.append({
            "label": "Validated By",
            "value": validated_by_value
        })
        
        # Display structured features in grid (3 columns) - with theme-adaptive card backgrounds
        cols = st.columns(3)
        for i, feature in enumerate(structured_features):
            col = cols[i % 3]
            with col:
                st.markdown(
                    f"""
                    <div style='border:1px solid rgba(128, 128, 128, 0.2);padding:10px;border-radius:8px;"
                    "background-color:transparent;margin-bottom:10px;'>
                        <b>{feature['label']}</b><br>
                        {feature['value']}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        
        st.divider()
        
        # ----- UNSTRUCTURED FEATURES -----
        st.subheader("📝 Unstructured Features")
        
        unstructured_features = []
        
        # Sentiment
        if 'sentiment' in selected_case:
            sentiment_value = selected_case.get('sentiment', 'N/A')
            unstructured_features.append({
                "label": "Sentiment",
                "value": sentiment_value
            })
        
        # Fraud Terms
        if 'fraud_terms' in selected_case:
            fraud_terms_value = selected_case.get('fraud_terms', 'N/A')
            unstructured_features.append({
                "label": "Fraud Terms",
                "value": fraud_terms_value
            })
        
        # Complaint Link - Check if complaint_link exists in fraud_cases table
        if 'complaint_link' in selected_case:
            complaint_link = selected_case.get('complaint_link', 'N/A')
            if complaint_link and str(complaint_link).strip() and complaint_link != 'N/A':
                unstructured_features.append({
                    "label": "Complaint Link",
                    "value": "✅ Linked to Complaint"
                })
            else:
                unstructured_features.append({
                    "label": "Complaint Link",
                    "value": "❌ No Complaint Link"
                })
        
        # Display unstructured features in grid (3 columns) - with theme-adaptive card backgrounds
        cols = st.columns(3)
        for i, feature in enumerate(unstructured_features):
            col = cols[i % 3]
            with col:
                st.markdown(
                    f"""
                    <div style='border:1px solid rgba(128, 128, 128, 0.2);padding:10px;border-radius:8px;"
                    "background-color:transparent;margin-bottom:10px;'>
                        <b>{feature['label']}</b><br>
                        {feature['value']}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
    
    # --------------------------
    # TAB 3: NLP ANALYSIS
    # --------------------------
    with tab3:
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
    
    # --------------------------
    # TAB 4: MODEL EXPLAINABILITY (SHAP)
    # --------------------------
    with tab4:
        st.write(f"Model explainability for **{selected_case_id}**")
        
        # Create a progress bar for risk score (using percentage)
        st.markdown(f"**Risk Score: {risk_percentage}**")
        st.progress(risk_score)
        
        # Simple feature importance visualization
        st.markdown("**Top contributing factors:**")
        st.write(f"**Will be implemented soon**: N/A")
    
    st.divider()