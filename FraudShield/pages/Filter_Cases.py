import streamlit as st
import pandas as pd
import numpy as np
from FraudShield.utils.supabase_client import supabase
from datetime import datetime

def show():
    # --------------------------
    # PAGE HEADER
    # --------------------------
    st.title("🔍 Filter Fraud Cases")
    st.caption("Filter and analyze fraud case data")

    # --------------------------
    # PAGE STYLES
    # --------------------------
    st.markdown("""
        <style>
            .card {
                background-color: white;
                border-radius: 10px;
                padding: 20px;
                box-shadow: 0 2px 6px rgba(0,0,0,0.05);
                margin-bottom: 20px;
            }
            .badge {
                display: inline-block;
                padding: 4px 8px;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 600;
                margin-right: 5px;
                margin-bottom: 4px;
            }
            .high { background-color: #fee2e2; color: #991b1b; }
            .medium { background-color: #ffedd5; color: #9a3412; }
            .low { background-color: #dcfce7; color: #166534; }
            .fraud { background-color: #fef2f2; color: #dc2626; border: 1px solid #fca5a5; }
            .legit { background-color: #f0fdf4; color: #16a34a; border: 1px solid #86efac; }
            .pending { background-color: #fff3cd; color: #856404; border: 1px solid #ffeeba; }
        </style>
    """, unsafe_allow_html=True)

    # --------------------------
    # HELPER FUNCTIONS
    # --------------------------
    def extract_risk_score(risk_display):
        """Convert risk display like 'High (0.85)' to float."""
        try:
            if pd.isna(risk_display):
                return 0.5
            if '(' in str(risk_display):
                return float(str(risk_display).split('(')[1].rstrip(')'))
            return 0.5
        except:
            return 0.5

    def extract_amount(amount_formatted):
        """Convert formatted amount like 'RM 8,500' to float."""
        try:
            if pd.isna(amount_formatted):
                return 0.0
            return float(str(amount_formatted).replace('RM', '').replace(',', '').replace('$', '').strip())
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
                return 'Unknown'
        except:
            return 'Unknown'

    # --------------------------
    # LOAD DATA FROM SUPABASE
    # --------------------------
    @st.cache_data(ttl=300, max_entries=1)
    def load_fraud_cases():
        """Load all fraud cases from Supabase with pagination."""
        try:
            all_data = []
            page = 0
            page_size = 1000
            total_loaded = 0
            
            while True:
                from_range = page * page_size
                to_range = from_range + page_size - 1
                
                response = supabase.table("fraud_cases") \
                    .select("*") \
                    .range(from_range, to_range) \
                    .execute()
                
                if not response.data:
                    break
                    
                all_data.extend(response.data)
                total_loaded = len(all_data)
                
                if len(response.data) < page_size:
                    break
                    
                page += 1
            
            if all_data:
                df = pd.DataFrame(all_data)
                
                # Process the data
                if 'transaction_date' in df.columns:
                    df['transaction_date'] = pd.to_datetime(df['transaction_date'])
                    df['date'] = df['transaction_date'].dt.date
                    df['date_str'] = df['transaction_date'].dt.strftime('%Y-%m-%d')
                
                # Extract numeric values for filtering and calculations
                df['risk_score_numeric'] = df['risk_display'].apply(extract_risk_score)
                df['amount_numeric'] = df['amount_formatted'].apply(extract_amount)
                df['risk_level'] = df['risk_display'].apply(get_risk_level)
                
                # Create fraud status based on actual_fraud column
                def get_fraud_status(actual_fraud):
                    if pd.isna(actual_fraud) or actual_fraud == '':
                        return 'Pending'
                    elif actual_fraud == 'confirmed':
                        return 'Fraudulent'
                    elif actual_fraud == 'rejected':
                        return 'Legitimate'
                    else:
                        return 'Pending'
                
                df['fraud_status'] = df['actual_fraud'].apply(get_fraud_status)
                
                # For fraud_label (for statistics)
                df['fraud_label'] = df['actual_fraud'].apply(lambda x: 1 if x == 'confirmed' else 0)
                
                return df, total_loaded, None
            else:
                return get_sample_data(), 0, "No data found in the database"
                
        except Exception as e:
            error_msg = f"Error loading data from Supabase: {str(e)}"
            return get_sample_data(), 0, error_msg
    
    def get_sample_data():
        """Return sample data if Supabase is unavailable."""
        # Create sample data matching your statistics
        np.random.seed(42)
        n_samples = 50000
        
        sample_data = {
            'case_id': [f'FR-2025-{i:04d}' for i in range(1000, 1000+n_samples)],
            'transaction_date': pd.date_range(start='2023-01-01', periods=n_samples, freq='h')[:n_samples],
            'amount_formatted': [f"RM {np.random.uniform(10, 50000):,.2f}" for _ in range(n_samples)],
            'risk_display': np.random.choice(['Low (0.15)', 'Medium (0.45)', 'High (0.85)'], n_samples, p=[0.3, 0.4, 0.3]),
            'sentiment': np.random.choice(['Positive', 'Neutral', 'Negative'], n_samples),
            'fraud_terms': np.random.choice(['scam', 'fraud', 'unauthorized', 'chargeback', ' dispute'], n_samples),
            'complaint_link': np.random.choice(['Trustpilot', 'Twitter', 'Reddit', 'Facebook'], n_samples),
            'customer_history': np.random.choice(['New', 'Existing', 'VIP'], n_samples),
            'actual_fraud': np.random.choice(['confirmed', 'rejected', ''], n_samples, p=[0.15, 0.7, 0.15]),
        }
        
        df = pd.DataFrame(sample_data)
        
        # Process the data
        df['transaction_date'] = pd.to_datetime(df['transaction_date'])
        df['date'] = df['transaction_date'].dt.date
        df['date_str'] = df['transaction_date'].dt.strftime('%Y-%m-%d')
        df['risk_score_numeric'] = df['risk_display'].apply(extract_risk_score)
        df['amount_numeric'] = df['amount_formatted'].apply(extract_amount)
        df['risk_level'] = df['risk_display'].apply(get_risk_level)
        
        def get_fraud_status(actual_fraud):
            if pd.isna(actual_fraud) or actual_fraud == '':
                return 'Pending'
            elif actual_fraud == 'confirmed':
                return 'Fraudulent'
            elif actual_fraud == 'rejected':
                return 'Legitimate'
            else:
                return 'Pending'
        
        df['fraud_status'] = df['actual_fraud'].apply(get_fraud_status)
        df['fraud_label'] = df['actual_fraud'].apply(lambda x: 1 if x == 'confirmed' else 0)
        
        return df

    # --------------------------
    # LOAD DATA WITH PROGRESS INDICATOR
    # --------------------------
    if 'data_loaded' not in st.session_state:
        st.session_state.data_loaded = False
    
    # Show loading spinner
    with st.spinner("Loading fraud case data from database..."):
        df, total_loaded, error = load_fraud_cases()
    
    # Show results/errors after loading
    if error:
        if "No data found" in error:
            st.warning("No data found in the database. Using sample data.")
        else:
            st.error(error)
            st.info("Using sample data for demonstration.")
    
    if total_loaded > 0 and not st.session_state.data_loaded:
        st.success(f"✅ Loaded {total_loaded:,} records from database")
        st.session_state.data_loaded = True

    # --------------------------
    # GET UNIQUE VALUES FOR FILTERS
    # --------------------------
    risk_levels = ["All", "High", "Medium", "Low", "Unknown"]
    fraud_statuses = ["All", "Fraudulent", "Legitimate", "Pending"]
    sentiments = ["All"] + sorted(df['sentiment'].dropna().unique().tolist()) if 'sentiment' in df.columns else ["All"]
    
    # Get unique dates
    if 'date_str' in df.columns:
        unique_dates = ["All"] + sorted(df['date_str'].dropna().unique().tolist(), reverse=True)
    else:
        unique_dates = ["All"]

    # --------------------------
    # FILTERS SECTION
    # --------------------------
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("🔍 Filter Fraud Cases")
    
    # First row of filters
    col1, col2, col3 = st.columns(3)
    with col1:
        case_id_search = st.text_input(
            "Case ID",
            placeholder="Search by Case ID (e.g., FR-2025-0842)",
            help="Enter full or partial case ID",
            key="filter_case_id"
        )
    
    with col2:
        risk_filter = st.selectbox(
            "Risk Level",
            risk_levels,
            key="filter_risk"
        )
    
    with col3:
        sentiment_filter = st.selectbox(
            "Sentiment",
            sentiments,
            key="filter_sentiment"
        )
    
    # Second row of filters
    col4, col5, col6 = st.columns(3)
    with col4:
        date_options = ["Select from list", "Enter manually"]
        date_option = st.selectbox("Date Filter Method", date_options, key="date_method")
        
        if date_option == "Select from list":
            date_filter = st.selectbox("Select Date", unique_dates, key="date_select")
        else:
            manual_date = st.text_input(
                "Enter Date (YYYY-MM-DD)",
                placeholder="e.g., 2023-08-14",
                help="Format: YYYY-MM-DD",
                key="date_manual"
            )
            date_filter = manual_date if manual_date else "All"
    
    with col5:
        fraud_filter = st.selectbox(
            "Fraud Status",
            fraud_statuses,
            key="filter_fraud"
        )
    
    with col6:
        if 'amount_numeric' in df.columns:
            min_amount = float(df['amount_numeric'].min())
            max_amount = float(df['amount_numeric'].max())
            amount_range = st.slider(
                "Amount Range (RM)",
                min_value=min_amount,
                max_value=max_amount,
                value=(min_amount, max_amount),
                help=f"Range: RM {min_amount:,.2f} - RM {max_amount:,.2f}",
                key="filter_amount",
                format="RM %.0f"
            )
        else:
            amount_range = (0, 100000)

    # --------------------------
    # FILTERING LOGIC
    # --------------------------
    filtered_df = df.copy()
    
    # Apply all filters automatically
    if case_id_search:
        filtered_df = filtered_df[
            filtered_df['case_id'].str.contains(
                case_id_search, 
                case=False, 
                na=False
            )
        ]
    
    if risk_filter != "All":
        filtered_df = filtered_df[filtered_df['risk_level'] == risk_filter]
    
    if sentiment_filter != "All" and 'sentiment' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['sentiment'] == sentiment_filter]
    
    if date_filter != "All" and date_filter and 'date_str' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['date_str'] == date_filter]
    
    if fraud_filter != "All":
        filtered_df = filtered_df[filtered_df['fraud_status'] == fraud_filter]
    
    if 'amount_numeric' in filtered_df.columns:
        filtered_df = filtered_df[
            (filtered_df['amount_numeric'] >= amount_range[0]) & 
            (filtered_df['amount_numeric'] <= amount_range[1])
        ]

    # Display filter summary
    st.markdown(f"**📊 Results:** {len(filtered_df):,} cases found (out of {len(df):,} total)")
    st.markdown("</div>", unsafe_allow_html=True)

    # --------------------------
    # RESULTS DISPLAY
    # --------------------------
    if len(filtered_df) == 0:
        st.warning("No cases match your filters. Try adjusting your criteria.")
    else:
        # Summary statistics
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("📈 Summary Statistics")
        
        # Calculate statistics
        total_amount = filtered_df['amount_numeric'].sum() if 'amount_numeric' in filtered_df.columns else 0
        avg_risk = filtered_df['risk_score_numeric'].mean() if 'risk_score_numeric' in filtered_df.columns else 0
        fraud_count = filtered_df[filtered_df['fraud_label'] == 1].shape[0] if 'fraud_label' in filtered_df.columns else 0
        fraud_rate = (fraud_count / len(filtered_df)) * 100 if len(filtered_df) > 0 else 0
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Amount", f"RM {total_amount:,.2f}")
        
        with col2:
            st.metric("Avg Risk Score", f"{avg_risk:.3f}")
        
        with col3:
            st.metric("Fraud Cases", f"{fraud_count:,}")
        
        with col4:
            st.metric("Fraud Rate", f"{fraud_rate:.1f}%")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Detailed results
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("📋 Case Details")
        
        show_options = st.radio(
            "View Options:",
            ["Table View", "Card View"],
            horizontal=True,
            label_visibility="collapsed"
        )
        
        if show_options == "Table View":
            # Select columns for table view
            table_columns = ['case_id', 'date_str', 'amount_formatted', 'risk_display', 
                           'sentiment', 'fraud_status']
            available_columns = [col for col in table_columns if col in filtered_df.columns]
            
            table_df = filtered_df[available_columns].copy()
            
            # Rename columns for display
            column_names = {
                'case_id': 'Case ID',
                'date_str': 'Date',
                'amount_formatted': 'Amount',
                'risk_display': 'Risk',
                'sentiment': 'Sentiment',
                'fraud_status': 'Status'
            }
            table_df = table_df.rename(columns={k: v for k, v in column_names.items() if k in table_df.columns})
            
            st.dataframe(table_df, use_container_width=True, hide_index=True)
        else:
            # Card view - limit to 5 cards
            display_count = min(5, len(filtered_df))
            if len(filtered_df) > 5:
                st.info(f"Showing first {display_count} of {len(filtered_df)} cases")
            
            for i, (_, row) in enumerate(filtered_df.iterrows()):
                if i >= 5:
                    break
                
                # Determine badge classes
                risk_class = row['risk_level'].lower() if 'risk_level' in row else 'unknown'
                
                if 'fraud_status' in row:
                    if row['fraud_status'] == 'Fraudulent':
                        fraud_class = 'fraud'
                    elif row['fraud_status'] == 'Legitimate':
                        fraud_class = 'legit'
                    else:
                        fraud_class = 'pending'
                else:
                    fraud_class = 'pending'
                
                with st.container():
                    col1, col2 = st.columns([3, 2])
                    
                    with col1:
                        st.markdown(f"**{row.get('case_id', 'N/A')}**")
                        if 'sentiment' in row:
                            st.caption(f"Sentiment: {row['sentiment']}")
                    
                    with col2:
                        if 'risk_display' in row:
                            st.markdown(
                                f"<span class='badge {risk_class}'>{row['risk_display']}</span>",
                                unsafe_allow_html=True
                            )
                        if 'fraud_status' in row:
                            st.markdown(
                                f"<span class='badge {fraud_class}'>{row['fraud_status']}</span>",
                                unsafe_allow_html=True
                            )
                    
                    col3, col4, col5, col6 = st.columns(4)
                    with col3:
                        st.caption("📅 Date")
                        st.write(row.get('date_str', 'N/A'))
                    with col4:
                        st.caption("💰 Amount")
                        st.markdown(f"**{row.get('amount_formatted', 'N/A')}**")
                    with col5:
                        st.caption("🎯 Risk Score")
                        risk_score = row.get('risk_score_numeric', 0)
                        st.write(f"{risk_score:.3f}")
                    with col6:
                        st.caption("📊 Fraud Terms")
                        st.write(row.get('fraud_terms', 'N/A')[:10] + '...' if len(str(row.get('fraud_terms', ''))) > 10 else row.get('fraud_terms', 'N/A'))
                    
                    st.divider()
        
        # Download button
        st.download_button(
            label="📥 Download Filtered Data (CSV)",
            data=filtered_df.to_csv(index=False),
            file_name=f"filtered_fraud_cases_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
        
        st.markdown("</div>", unsafe_allow_html=True)

    # --------------------------
    # DATA MANAGEMENT
    # --------------------------
    with st.expander("⚙️ Data Information"):
        st.write(f"**Database:** {len(df):,} total cases")
        if 'date_str' in df.columns:
            st.write(f"**Date Range:** {df['date_str'].min()} to {df['date_str'].max()}")
        if 'risk_level' in df.columns:
            st.write(f"**Risk Distribution:** {df['risk_level'].value_counts().to_dict()}")
        
        if st.button("🔄 Refresh Data", type="secondary"):
            st.cache_data.clear()
            st.session_state.data_loaded = False
            st.rerun()