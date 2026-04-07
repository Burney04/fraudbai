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
    st.divider()
    st.markdown("""
        <style>
            .badge {
                display: inline-block;
                padding: 6px 12px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
                margin-right: 5px;
                margin-bottom: 4px;
            }
            .high { background-color: #fee2e2; color: #991b1b; }
            .medium { background-color: #ffedd5; color: #9a3412; }
            .low { background-color: #dcfce7; color: #166534; }
            .case-card {
                background-color: white;
                padding: 1.5rem;
                border-radius: 12px;
                border: 1px solid #e5e7eb;
                margin-bottom: 1rem;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                transition: transform 0.2s, box-shadow 0.2s;
            }
            .case-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            }
            .case-id {
                font-size: 1.2rem;
                font-weight: 700;
                color: #1f2937;
                margin-bottom: 0.75rem;
            }
            .case-detail {
                font-size: 1rem;
                margin-bottom: 0.5rem;
            }
            .case-detail strong {
                color: #4b5563;
                font-weight: 600;
            }
            .risk-score-container {
                margin-top: 0.75rem;
                margin-bottom: 0.5rem;
            }
            .stButton > button {
                padding: 0.25rem 1rem;
                font-size: 0.85rem;
            }
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
    # INITIALIZE SESSION STATE
    # --------------------------
    if 'data_loaded' not in st.session_state:
        st.session_state.data_loaded = False
    
    if 'apply_filters' not in st.session_state:
        st.session_state.apply_filters = False
    
    if 'reset_triggered' not in st.session_state:
        st.session_state.reset_triggered = False
    
    if 'original_df' not in st.session_state:
        st.session_state.original_df = None
    
    if 'filtered_df' not in st.session_state:
        st.session_state.filtered_df = None
    
    if 'form_version' not in st.session_state:
        st.session_state.form_version = 0
    
    if 'table_page' not in st.session_state:
        st.session_state.table_page = 0  # 0-indexed page number for table pagination

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
                
                # Extract numeric values for filtering and calculations
                df['risk_score_numeric'] = df['risk_display'].apply(extract_risk_score)
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
        
        sample_data = {
            'case_id': [f'FR-2025-{i:04d}' for i in range(1000, 1000+n_samples)],
            'transaction_date': pd.date_range(start='2023-01-01', periods=n_samples, freq='h')[:n_samples],
            'amount_formatted': [f"RM {np.random.uniform(10, 50000):,.2f}" for _ in range(n_samples)],
            'risk_display': np.random.choice(['Low (0.15)', 'Medium (0.45)', 'High (0.85)'], n_samples, p=[0.3, 0.4, 0.3]),
        }
        
        df = pd.DataFrame(sample_data)
        
        # Process the data
        df['transaction_date'] = pd.to_datetime(df['transaction_date'])
        df['date'] = df['transaction_date'].dt.date
        df['date_str'] = df['transaction_date'].dt.strftime('%Y-%m-%d')
        df['risk_score_numeric'] = df['risk_display'].apply(extract_risk_score)
        df['amount_numeric'] = df['amount_formatted'].apply(extract_amount)
        df['risk_level'] = df['risk_display'].apply(get_risk_level)
        
        return df

    # --------------------------
    # LOAD DATA WITH PROGRESS INDICATOR
    # --------------------------
    with st.spinner("Loading fraud case data from database (first 1000 records)..."):
        df, total_loaded, error = load_fraud_cases()
    
    # Store original dataframe
    if st.session_state.original_df is None:
        st.session_state.original_df = df.copy()
        st.session_state.filtered_df = df.copy()
    
    # Show results/errors after loading
    if error:
        if "No data found" in error:
            st.warning("No data found in the database. Using sample data.")
        else:
            st.error(error)
            st.info("Using sample data for demonstration.")
    
    if total_loaded > 0 and not st.session_state.data_loaded:
        st.success(f"✅ Loaded {total_loaded:,} records from database (limited to first 1000)")
        st.session_state.data_loaded = True

    # --------------------------
    # GET UNIQUE VALUES FOR FILTERS
    # --------------------------
    risk_levels = ["All", "High", "Medium", "Low", "Unknown"]
    
    # Get unique dates
    if 'date_str' in df.columns:
        unique_dates = ["All"] + sorted(df['date_str'].dropna().unique().tolist(), reverse=True)
    else:
        unique_dates = ["All"]
    
    # Get min and max amounts
    if 'amount_numeric' in df.columns:
        global_min_amount = float(df['amount_numeric'].min())
        global_max_amount = float(df['amount_numeric'].max())
    else:
        global_min_amount = 0
        global_max_amount = 100000

    # --------------------------
    # CHECK IF RESET IS TRIGGERED
    # --------------------------
    if st.session_state.reset_triggered:
        # Clear all filter-related session state
        st.session_state.apply_filters = False
        st.session_state.filtered_df = st.session_state.original_df.copy()
        # Increment form version to force widget reset
        st.session_state.form_version += 1
        # Reset table page
        st.session_state.table_page = 0
        # Clear the reset trigger
        st.session_state.reset_triggered = False
        # Force a rerun to refresh all inputs
        st.rerun()

    # --------------------------
    # FILTERS SECTION
    # --------------------------
    st.markdown("### 📊 Filter Cases")
    
    # Create unique keys based on form_version to force reset
    version = st.session_state.form_version
    
    # Create filter containers to store values
    with st.form("filter_form"):
        # First row of filters
        col1, col2 = st.columns(2)
        with col1:
            case_id_search = st.text_input(
                "Case ID",
                placeholder="Search by Case ID (e.g., FR-2025-0842)",
                help="Enter full or partial case ID",
                key=f"filter_case_id_{version}"
            )
        
        with col2:
            risk_filter = st.selectbox(
                "Risk Level",
                risk_levels,
                key=f"filter_risk_{version}"
            )
        
        # Second row of filters
        col3, col4 = st.columns(2)
        with col3:
            date_options = ["Select from list", "Enter manually"]
            date_option = st.selectbox(
                "Date Filter Method", 
                date_options, 
                key=f"date_method_{version}"
            )
            
            if date_option == "Select from list":
                date_filter = st.selectbox(
                    "Select Date", 
                    unique_dates, 
                    key=f"date_select_{version}"
                )
            else:
                manual_date = st.text_input(
                    "Enter Date (YYYY-MM-DD)",
                    placeholder="e.g., 2023-08-14",
                    help="Format: YYYY-MM-DD",
                    key=f"date_manual_{version}"
                )
                date_filter = manual_date if manual_date else "All"
        
        with col4:
            st.markdown("**Amount Range (RM)**")
            amount_col1, amount_col2 = st.columns(2)
            with amount_col1:
                min_amount_input = st.number_input(
                    "Min",
                    min_value=global_min_amount,
                    max_value=global_max_amount,
                    value=global_min_amount,
                    step=1000.0,
                    format="%.2f",
                    key=f"min_amount_{version}"
                )
            with amount_col2:
                max_amount_input = st.number_input(
                    "Max",
                    min_value=global_min_amount,
                    max_value=global_max_amount,
                    value=global_max_amount,
                    step=1000.0,
                    format="%.2f",
                    key=f"max_amount_{version}"
                )
            
            amount_range = (min_amount_input, max_amount_input)
        
        # Buttons row
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            apply_button = st.form_submit_button("🔍 Apply Filters", type="primary", use_container_width=True)
        with col_btn2:
            reset_button = st.form_submit_button("🔄 Reset All Filters", use_container_width=True)
        
        if apply_button:
            st.session_state.apply_filters = True
            st.session_state.table_page = 0  # Reset to first page when applying new filters
            st.rerun()
        
        if reset_button:
            # Set reset trigger
            st.session_state.reset_triggered = True
            st.rerun()

    # --------------------------
    # FILTERING LOGIC (Only applied when Apply button is clicked)
    # --------------------------
    if st.session_state.apply_filters and not st.session_state.reset_triggered:
        filtered_df = st.session_state.original_df.copy()
        
        # Apply all filters
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
        
        if date_filter != "All" and date_filter and 'date_str' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['date_str'] == date_filter]
        
        if 'amount_numeric' in filtered_df.columns:
            filtered_df = filtered_df[
                (filtered_df['amount_numeric'] >= amount_range[0]) & 
                (filtered_df['amount_numeric'] <= amount_range[1])
            ]
        
        # Store filtered results in session state
        st.session_state.filtered_df = filtered_df

    # Display filter summary
    st.divider()
    st.markdown(f"**📊 Results:** {len(st.session_state.filtered_df):,} cases found (out of {len(st.session_state.original_df):,} total)")

    # --------------------------
    # RESULTS DISPLAY
    # --------------------------
    if len(st.session_state.filtered_df) == 0:
        st.warning("No cases match your filters. Try adjusting your criteria.")
    else:
        st.divider()
        st.subheader("📋 Case Details")
        
        show_options = st.radio(
            "View Options:",
            ["Table View"],
            horizontal=True,
            label_visibility="collapsed"
        )
        
        if show_options == "Table View":
            # Select columns for table view
            table_columns = ['case_id', 'date_str', 'amount_formatted', 'risk_display']
            available_columns = [col for col in table_columns if col in st.session_state.filtered_df.columns]
            
            table_df = st.session_state.filtered_df[available_columns].copy()
            
            # Rename columns for display
            column_names = {
                'case_id': 'Case ID',
                'date_str': 'Date',
                'amount_formatted': 'Amount',
                'risk_display': 'Risk Score'
            }
            table_df = table_df.rename(columns={k: v for k, v in column_names.items() if k in table_df.columns})
            
            # Pagination settings
            ROWS_PER_PAGE = 10
            total_rows = len(table_df)
            total_pages = (total_rows + ROWS_PER_PAGE - 1) // ROWS_PER_PAGE
            
            # Ensure page is within bounds
            if total_pages > 0:
                if st.session_state.table_page >= total_pages:
                    st.session_state.table_page = total_pages - 1
                if st.session_state.table_page < 0:
                    st.session_state.table_page = 0
            else:
                st.session_state.table_page = 0
            
            # Get current page rows
            start_idx = st.session_state.table_page * ROWS_PER_PAGE
            end_idx = min(start_idx + ROWS_PER_PAGE, total_rows)
            current_page_df = table_df.iloc[start_idx:end_idx]
            
            # Display page info
            if total_pages > 0:
                st.markdown(f"**Page {st.session_state.table_page + 1} of {total_pages}** (Showing {start_idx + 1}-{end_idx} of {total_rows} cases)")
            
            # Display table with custom styling
            st.markdown("### Fraud Cases")
            
            # Create a container for the table
            for idx, row in current_page_df.iterrows():
                col1, col2, col3, col4, col5 = st.columns([2, 1.5, 1.5, 2, 1])
                with col1:
                    st.write(row['Case ID'])
                with col2:
                    st.write(row['Date'])
                with col3:
                    st.write(row['Amount'])
                with col4:
                    risk_display = row['Risk Score']
                    if 'High' in risk_display:
                        st.markdown(f'<span class="badge high">{risk_display}</span>', unsafe_allow_html=True)
                    elif 'Medium' in risk_display:
                        st.markdown(f'<span class="badge medium">{risk_display}</span>', unsafe_allow_html=True)
                    elif 'Low' in risk_display:
                        st.markdown(f'<span class="badge low">{risk_display}</span>', unsafe_allow_html=True)
                    else:
                        st.write(risk_display)
                with col5:
                    # Updated Inspect button with query parameter navigation
                    if st.button(f"🔍 Inspect", key=f"inspect_table_{row['Case ID']}_{start_idx + idx}", use_container_width=True):
                        st.session_state.selected_case_id = row['Case ID']
                        # Use query parameters to trigger navigation
                        st.query_params["page"] = "Drill-Down Inspection"
                        st.query_params["case_id"] = row['Case ID']
                        st.rerun()
                st.divider()
            
            # Pagination controls
            if total_pages > 1:
                st.markdown("---")
                
                # Create 3 columns for pagination controls
                col_prev, col_page_input, col_next = st.columns([1, 2, 1])
                
                # Previous button
                with col_prev:
                    if st.button("◀ Previous", use_container_width=True, disabled=(st.session_state.table_page == 0), key="table_prev"):
                        st.session_state.table_page -= 1
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
                            value=st.session_state.table_page + 1,
                            step=1,
                            label_visibility="collapsed",
                            key="table_page_number_input"
                        )
                    with input_col2:
                        if st.button("Go", use_container_width=True, key="table_go_to_page"):
                            if 1 <= page_number <= total_pages:
                                st.session_state.table_page = page_number - 1
                                st.rerun()
                
                # Next button
                with col_next:
                    if st.button("Next ▶", use_container_width=True, disabled=(st.session_state.table_page >= total_pages - 1), key="table_next"):
                        st.session_state.table_page += 1
                        st.rerun()
                
                # Show current page info
                st.markdown(f"<div style='text-align: center; margin-top: 8px; font-size: 0.85rem; color: #666;'>Page {st.session_state.table_page + 1} of {total_pages}</div>", unsafe_allow_html=True)
        
        # Download button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.download_button(
                label="📥 Download Filtered Data (CSV)",
                data=st.session_state.filtered_df.to_csv(index=False),
                file_name=f"filtered_fraud_cases_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )

    # --------------------------
    # DATA MANAGEMENT
    # --------------------------
    with st.expander("⚙️ Data Information"):
        st.write(f"**Total Cases:** {len(st.session_state.original_df):,} (limited to first 1000 records)")
        if 'date_str' in st.session_state.original_df.columns:
            st.write(f"**Date Range:** {st.session_state.original_df['date_str'].min()} to {st.session_state.original_df['date_str'].max()}")
        if 'risk_level' in st.session_state.original_df.columns:
            risk_dist = st.session_state.original_df['risk_level'].value_counts().to_dict()
            st.write(f"**Risk Distribution:** {risk_dist}")
        
        if st.button("🔄 Refresh Data", type="secondary"):
            st.cache_data.clear()
            st.session_state.data_loaded = False
            st.session_state.apply_filters = False
            st.session_state.reset_triggered = True
            st.session_state.original_df = None
            st.session_state.filtered_df = None
            st.session_state.table_page = 0
            st.rerun()