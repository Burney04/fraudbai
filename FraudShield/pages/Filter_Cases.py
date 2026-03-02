import streamlit as st
import pandas as pd
from FraudShield.utils.supabase_client import supabase
from datetime import datetime

def show():
    # --------------------------
    # PAGE HEADER
    # --------------------------
    st.title("🔍 Filter Transaction Records")
    st.caption("Filter and analyze transaction data for fraud detection")

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
        </style>
    """, unsafe_allow_html=True)

    # --------------------------
    # LOAD DATA FROM SUPABASE (WITH PAGINATION FOR 50K ROWS)
    # --------------------------
    @st.cache_data(ttl=300, max_entries=1)
    def load_transaction_data():
        """Load ALL transaction records from Supabase with pagination."""
        try:
            all_data = []
            page = 0
            page_size = 1000
            
            # Use a simple progress variable instead of st.toast
            total_loaded = 0
            
            while True:
                from_range = page * page_size
                to_range = from_range + page_size - 1
                
                response = supabase.table("transactions") \
                    .select("*") \
                    .range(from_range, to_range) \
                    .execute()
                
                if not response.data:
                    break
                    
                all_data.extend(response.data)
                total_loaded = len(all_data)
                
                # If we got less than page_size, we're done
                if len(response.data) < page_size:
                    break
                    
                page += 1
            
            if all_data:
                df = pd.DataFrame(all_data)
                
                # Process the data
                if 'timestamp' in df.columns:
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    df['date'] = df['timestamp'].dt.date
                    df['date_str'] = df['timestamp'].dt.strftime('%Y-%m-%d')
                
                # Add risk level categorization
                def categorize_risk(risk_score):
                    if pd.isna(risk_score):
                        return 'Unknown'
                    elif risk_score < 0.3:
                        return 'Low'
                    elif risk_score < 0.6:
                        return 'Medium'
                    else:
                        return 'High'
                
                if 'risk_score' in df.columns:
                    df['risk_level'] = df['risk_score'].apply(categorize_risk)
                
                # Format amount
                if 'transaction_amount' in df.columns:
                    df['formatted_amount'] = df['transaction_amount'].apply(lambda x: f"${float(x):,.2f}")
                
                # Format fraud label
                if 'fraud_label' in df.columns:
                    df['fraud_status'] = df['fraud_label'].apply(lambda x: 'Fraudulent' if x == 1 else 'Legitimate')
                
                return df, total_loaded, None  # Return df, count, and error
            else:
                return get_sample_data(), 0, "No data found in the database"
                
        except Exception as e:
            error_msg = f"Error loading data from Supabase: {str(e)}"
            return get_sample_data(), 0, error_msg
    
    def get_sample_data():
        """Return sample data if Supabase is unavailable."""
        sample_data = {
            'transaction_id': ['TXN_33553', 'TXN_9427', 'TXN_199', 'TXN_12447', 'TXN_39489',
                              'TXN_42724', 'TXN_10822', 'TXN_49498', 'TXN_4144', 'TXN_36958'],
            'user_id': ['USER_1834', 'USER_7875', 'USER_2734', 'USER_2617', 'USER_2014',
                       'USER_6852', 'USER_5052', 'USER_4660', 'USER_1584', 'USER_9498'],
            'transaction_amount': [39.79, 1.19, 28.96, 254.32, 31.28, 168.55, 3.79, 7.08, 34.25, 16.24],
            'transaction_type': ['POS', 'Bank Transfer', 'Online', 'ATM Withdrawal', 'POS',
                                'Online', 'POS', 'ATM Withdrawal', 'ATM Withdrawal', 'POS'],
            'timestamp': pd.to_datetime(['2023-08-14 19:30:00', '2023-06-07 04:01:00', '2023-06-20 15:25:00',
                                        '2023-12-07 00:31:00', '2023-11-11 23:44:00', '2023-06-05 20:55:00',
                                        '2023-11-07 01:18:00', '2023-02-25 03:43:00', '2023-03-09 22:51:00',
                                        '2023-09-20 17:27:00']),
            'risk_score': [0.8494, 0.0959, 0.84, 0.7935, 0.3819, 0.0504, 0.0875, 0.5326, 0.1347, 0.3394],
            'fraud_label': [0, 1, 1, 1, 1, 0, 0, 1, 0, 0]
        }
        
        df = pd.DataFrame(sample_data)
        df['date'] = df['timestamp'].dt.date
        df['date_str'] = df['timestamp'].dt.strftime('%Y-%m-%d')
        df['risk_level'] = df['risk_score'].apply(lambda x: 'Low' if x < 0.3 else 'Medium' if x < 0.6 else 'High')
        df['formatted_amount'] = df['transaction_amount'].apply(lambda x: f"${x:,.2f}")
        df['fraud_status'] = df['fraud_label'].apply(lambda x: 'Fraudulent' if x == 1 else 'Legitimate')
        
        return df

    # --------------------------
    # LOAD DATA WITH PROGRESS INDICATOR
    # --------------------------
    if 'data_loaded' not in st.session_state:
        st.session_state.data_loaded = False
    
    # Show loading spinner
    with st.spinner("Loading transaction data from database..."):
        df, total_loaded, error = load_transaction_data()
    
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
    transaction_types = ["All"] + sorted(df['transaction_type'].dropna().unique().tolist())
    unique_dates = ["All"] + sorted(df['date_str'].dropna().unique().tolist(), reverse=True)
    risk_levels = ["All", "Low", "Medium", "High"]
    fraud_statuses = ["All", "Fraudulent", "Legitimate"]

    # --------------------------
    # FILTERS SECTION
    # --------------------------
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("🔍 Filter Transactions")
    
    # First row of filters
    col1, col2, col3 = st.columns(3)
    with col1:
        transaction_id_search = st.text_input(
            "Transaction ID",
            placeholder="Search by TXN_ID (e.g., TXN_33553)",
            help="Enter full or partial transaction ID",
            key="filter_txn_id"
        )
    
    with col2:
        risk_filter = st.selectbox(
            "Risk Level",
            risk_levels,
            help="Low: 0-0.29, Medium: 0.3-0.59, High: ≥0.6",
            key="filter_risk"
        )
    
    with col3:
        transaction_type_filter = st.selectbox(
            "Transaction Type",
            transaction_types,
            help="Filter by transaction method",
            key="filter_type"
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
            help="Filter by fraud classification",
            key="filter_fraud"
        )
    
    with col6:
        if 'transaction_amount' in df.columns:
            min_amount = float(df['transaction_amount'].min())
            max_amount = float(df['transaction_amount'].max())
            amount_range = st.slider(
                "Amount Range ($)",
                min_value=min_amount,
                max_value=max_amount,
                value=(min_amount, max_amount),
                help=f"Range: ${min_amount:.2f} - ${max_amount:.2f}",
                key="filter_amount"
            )
        else:
            amount_range = (0, 1000)

    # --------------------------
    # FILTERING LOGIC
    # --------------------------
    filtered_df = df.copy()
    
    # Apply all filters automatically
    if transaction_id_search:
        filtered_df = filtered_df[
            filtered_df['transaction_id'].str.contains(
                transaction_id_search, 
                case=False, 
                na=False
            )
        ]
    
    if risk_filter != "All":
        filtered_df = filtered_df[filtered_df['risk_level'] == risk_filter]
    
    if transaction_type_filter != "All":
        filtered_df = filtered_df[filtered_df['transaction_type'] == transaction_type_filter]
    
    if date_filter != "All" and date_filter:
        filtered_df = filtered_df[filtered_df['date_str'] == date_filter]
    
    if fraud_filter != "All":
        filtered_df = filtered_df[filtered_df['fraud_status'] == fraud_filter]
    
    filtered_df = filtered_df[
        (filtered_df['transaction_amount'] >= amount_range[0]) & 
        (filtered_df['transaction_amount'] <= amount_range[1])
    ]

    # Display filter summary
    st.markdown(f"**📊 Results:** {len(filtered_df):,} transactions found (out of {len(df):,} total)")

    # --------------------------
    # RESULTS DISPLAY
    # --------------------------
    if len(filtered_df) == 0:
        st.warning("No transactions match your filters. Try adjusting your criteria.")
    else:
        # Summary statistics
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("📈 Summary Statistics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_amount = filtered_df['transaction_amount'].sum()
            st.metric("Total Amount", f"${total_amount:,.2f}")
        
        with col2:
            avg_risk = filtered_df['risk_score'].mean()
            st.metric("Avg Risk Score", f"{avg_risk:.3f}")
        
        with col3:
            fraud_count = filtered_df[filtered_df['fraud_label'] == 1].shape[0]
            st.metric("Fraud Cases", f"{fraud_count:,}")
        
        with col4:
            fraud_rate = (fraud_count / len(filtered_df)) * 100 if len(filtered_df) > 0 else 0
            st.metric("Fraud Rate", f"{fraud_rate:.1f}%")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Detailed results
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("📋 Transaction Details")
        
        show_options = st.radio(
            "View Options:",
            ["Table View", "Card View"],
            horizontal=True,
            label_visibility="collapsed"
        )
        
        if show_options == "Table View":
            table_df = filtered_df[[
                'transaction_id', 'date_str', 'transaction_type', 
                'formatted_amount', 'risk_level', 'fraud_status'
            ]].copy()
            table_df.columns = ['Transaction ID', 'Date', 'Type', 'Amount', 'Risk Level', 'Status']
            st.dataframe(table_df, use_container_width=True)
        else:
            # Card view - limit to 5 cards
            display_count = min(5, len(filtered_df))
            if len(filtered_df) > 5:
                st.info(f"Showing first {display_count} of {len(filtered_df)} transactions")
            
            for i, (_, row) in enumerate(filtered_df.iterrows()):
                if i >= 5:  # Limit to 5 cards
                    break
                    
                risk_class = row['risk_level'].lower()
                fraud_class = "fraud" if row['fraud_label'] == 1 else "legit"
                
                with st.container():
                    col1, col2 = st.columns([3, 2])
                    
                    with col1:
                        st.markdown(f"**{row['transaction_id']}**")
                        st.caption(f"User: {row['user_id']}")
                    
                    with col2:
                        st.markdown(
                            f"<span class='badge {risk_class}'>{row['risk_level']} Risk ({row['risk_score']:.3f})</span>",
                            unsafe_allow_html=True
                        )
                        st.markdown(
                            f"<span class='badge {fraud_class}'>{row['fraud_status']}</span>",
                            unsafe_allow_html=True
                        )
                    
                    col3, col4, col5, col6 = st.columns(4)
                    with col3:
                        st.caption("📅 Date")
                        st.write(row['date_str'])
                    with col4:
                        st.caption("💳 Type")
                        st.write(row['transaction_type'])
                    with col5:
                        st.caption("💰 Amount")
                        st.markdown(f"**{row['formatted_amount']}**")
                    with col6:
                        st.caption("🎯 Score")
                        st.write(f"{row['risk_score']:.4f}")
                    
                    st.divider()
        
        # Download button
        st.download_button(
            label="📥 Download Filtered Data (CSV)",
            data=filtered_df.to_csv(index=False),
            file_name=f"filtered_transactions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
        
        st.markdown("</div>", unsafe_allow_html=True)

    # --------------------------
    # DATA MANAGEMENT
    # --------------------------
    with st.expander("⚙️ Data Information"):
        st.write(f"**Database:** {len(df):,} total transactions")
        st.write(f"**Date Range:** {df['date_str'].min()} to {df['date_str'].max()}")
        st.write(f"**Transaction Types:** {', '.join(df['transaction_type'].unique()[:5])}{'...' if len(df['transaction_type'].unique()) > 5 else ''}")
        
        if st.button("🔄 Refresh Data", type="secondary"):
            # Clear cache and reset loaded state
            st.cache_data.clear()
            st.session_state.data_loaded = False
            st.rerun()