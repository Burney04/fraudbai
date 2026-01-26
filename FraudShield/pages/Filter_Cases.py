import streamlit as st
import pandas as pd

def show():
    # --------------------------
    # PAGE HEADER
    # --------------------------
    st.title("🧾 Filter Fraud Cases")
    st.caption("Narrow down and inspect fraud alerts using smart filters")

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
            }
            .high { background-color: #fee2e2; color: #991b1b; }
            .medium { background-color: #ffedd5; color: #9a3412; }
            .low { background-color: #dcfce7; color: #166534; }
            .keyword { background-color: #fff7ed; color: #9a3412; border: 1px solid #fed7aa; }
        </style>
    """, unsafe_allow_html=True)

    # --------------------------
    # MOCK DATA
    # --------------------------
    data = [
        {"Case ID": "FR-2025-0842", "Date": "2025-10-12", "Amount": 8500, "Risk Score": 0.92, "Status": "High", "Keywords": ["urgent transfer", "verify account"], "Bank": "Maybank"},
        {"Case ID": "FR-2025-0841", "Date": "2025-10-12", "Amount": 3200, "Risk Score": 0.78, "Status": "Medium", "Keywords": ["suspicious activity"], "Bank": "CIMB"},
        {"Case ID": "FR-2025-0840", "Date": "2025-10-11", "Amount": 12300, "Risk Score": 0.95, "Status": "High", "Keywords": ["unauthorized", "fraud alert"], "Bank": "Public Bank"},
        {"Case ID": "FR-2025-0839", "Date": "2025-10-11", "Amount": 1850, "Risk Score": 0.65, "Status": "Medium", "Keywords": ["account locked"], "Bank": "RHB Bank"},
        {"Case ID": "FR-2025-0838", "Date": "2025-10-10", "Amount": 5600, "Risk Score": 0.88, "Status": "High", "Keywords": ["unusual transaction", "immediate action"], "Bank": "Hong Leong Bank"},
        {"Case ID": "FR-2025-0837", "Date": "2025-10-10", "Amount": 920, "Risk Score": 0.71, "Status": "Medium", "Keywords": ["verify account"], "Bank": "AmBank"},
    ]
    df = pd.DataFrame(data)

    # --------------------------
    # FILTERS SECTION
    # --------------------------
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("🔍 Filters")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        search_term = st.text_input("Search Case ID / Keywords", placeholder="FR-2025-0842 or 'urgent'")
    with col2:
        risk_filter = st.selectbox("Risk Level", ["All", "High", "Medium", "Low"])
    with col3:
        bank_filter = st.selectbox("Bank", ["All", "Maybank", "CIMB", "Public Bank", "RHB Bank", "Hong Leong Bank", "AmBank"])
    with col4:
        date_filter = st.selectbox("Date", ["All", "2025-10-12", "2025-10-11", "2025-10-10"])

    clear = st.button("🔄 Clear Filters")
    if clear:
        st.rerun()

    # --------------------------
    # FILTERING LOGIC
    # --------------------------
    filtered_df = df[
        df.apply(lambda row: (
            (search_term.lower() in row["Case ID"].lower() or any(search_term.lower() in kw.lower() for kw in row["Keywords"]))
            if search_term else True
        ) and
        (risk_filter == "All" or row["Status"].lower() == risk_filter.lower()) and
        (bank_filter == "All" or row["Bank"] == bank_filter) and
        (date_filter == "All" or row["Date"] == date_filter),
        axis=1
    )]

    st.caption(f"✅ {len(filtered_df)} cases found")
    st.markdown("</div>", unsafe_allow_html=True)

    # --------------------------
    # RESULTS TABLE
    # --------------------------
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("📋 Filtered Cases")

    if filtered_df.empty:
        st.warning("No matching cases found.")
    else:
        for _, row in filtered_df.iterrows():
            risk_class = "high" if row["Status"] == "High" else "medium" if row["Status"] == "Medium" else "low"
            st.markdown(f"""
                <div style='padding:10px 0; border-bottom:1px solid #f3f4f6;'>
                    <strong>{row["Case ID"]}</strong> ({row["Date"]}) - <em>{row["Bank"]}</em><br>
                    💰 <b>RM {row["Amount"]:,}</b> | 
                    <span class='badge {risk_class}'>{row["Risk Score"]*100:.0f}% - {row["Status"]}</span><br>
                    {" ".join([f"<span class='badge keyword'>{kw}</span>" for kw in row["Keywords"]])}
                    <div style='text-align:right; margin-top:4px;'>
                        <button style='background-color:white; border:1px solid #d1d5db; border-radius:6px; padding:4px 8px; cursor:pointer;'>Inspect</button>
                    </div>
                </div>
            """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)