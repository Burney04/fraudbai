import streamlit as st
import plotly.express as px
import pandas as pd

def render_reports():
    st.title("📊 Fraud Detection Reports")
    st.caption("Comprehensive fraud analytics with explainability insights")
    st.divider()

    # --- Controls ---
    period = st.selectbox("Select Period", ["1 month", "3 months", "6 months", "1 year"], index=2)
    st.write(f"Currently viewing **{period}** trend.")
    export = st.button("Export Report")
    st.divider()

    # --- KPI Cards ---
    stats = [
        {"title": "Total Transactions", "value": "52,340", "change": 15.3},
        {"title": "Flagged Cases", "value": 142, "change": -8.2},
        {"title": "Validated Cases", "value": 98, "change": 12.5},
        {"title": "Amount Saved (RM)", "value": "932K", "change": 15.0},
        {"title": "Threats Detected", "value": 337, "change": 8.0},
    ]

    cols = st.columns(len(stats))
    for col, stat in zip(cols, stats):
        color_mode = "inverse" if stat["title"] == "Threats Detected" else "normal"
        with col:
            st.metric(
                label=stat["title"],
                value=stat["value"],
                delta=f"{stat['change']}%",
                delta_color=color_mode,
            )

    st.divider()

    # --- Data Visualization ---
    fraud_trend = pd.DataFrame({
        "Month": ["Apr", "May", "Jun", "Jul", "Aug", "Sep"],
        "Detected": [45, 52, 38, 61, 73, 68],
        "Prevented": [42, 48, 35, 58, 69, 64],
        "Saved (MYR)": [125_000, 142_000, 98_000, 168_000, 210_000, 189_000],
    })

    geo_data = pd.DataFrame({
        "Region": ["Kuala Lumpur", "Penang", "Johor", "Sabah", "Sarawak"],
        "Cases": [120, 78, 65, 43, 59],
    })

    validation_data = pd.DataFrame({
        "Outcome": ["Confirmed Fraud", "Rejected (Legitimate)", "Escalated", "Pending"],
        "Cases": [98, 127, 23, 42],
        "Color": ["#ef4444", "#22c55e", "#f97316", "#a855f7"],
    })

    shap_data = pd.DataFrame({
        "Feature": [
            "Transaction Amount > RM 5,000", "Off-hours Transaction",
            "Location Change > 200km", "Keyword: urgent transfer",
            "Customer Tenure > 2 years"
        ],
        "SHAP Value": [0.38, 0.32, 0.29, 0.24, -0.19],
    })

    nlp_keywords = pd.DataFrame({
        "Keyword": ["urgent transfer", "verify account", "suspicious activity",
                    "account locked", "unauthorized", "fraud alert"],
        "Frequency": [89, 76, 64, 52, 48, 41],
        "Risk Increase (%)": [24, 21, 18, 16, 15, 14],
        "SHAP Contribution": [0.24, 0.21, 0.18, 0.16, 0.15, 0.14],
    })

    # --- Tabs ---
    st.markdown(
        """
        <style>
        div[data-baseweb="tab-list"] {
            display: flex;
            justify-content: space-between;
            width: 95%;
            margin: 0 auto;
            padding: 0 1rem;
        }
        div[data-baseweb="tab"] {
            flex-grow: 1 !important;
            text-align: center !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Fraud Trends", "🗺️ Geography", "✅ Validation", "🎯 SHAP Summary", "🧠 NLP Keywords"
    ])

    # ---- Tab 1 ----
    with tab1:
        col1, _, col2 = st.columns([1, 0.05, 1])
        with col1:
            st.subheader("Fraud Detection Trends")
            st.caption("Monthly fraud detection and prevention statistics")

            fig = px.line(
                fraud_trend, x="Month", y=["Detected", "Prevented"],
                markers=True, title="Detected vs Prevented Fraud Cases",
                color_discrete_map={"Detected": "#ef4444", "Prevented": "#22c55e"},
            )
            fig.update_layout(
                legend=dict(orientation="h", yanchor="top", y=-0.3, xanchor="center", x=0.5, title=None),
                margin=dict(b=60)
            )
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            st.subheader("💰 Amount Saved (MYR)")
            st.plotly_chart(
                px.area(fraud_trend, x="Month", y="Saved (MYR)", title="Total Amount Saved", color_discrete_sequence=["#22c55e"]),
                use_container_width=True,
            )

    # ---- Tab 2 ----
    with tab2:
        st.subheader("Geographic Fraud Trends")
        st.plotly_chart(
            px.bar(geo_data, x="Region", y="Cases", color="Cases", title="Fraud Cases by Region", color_continuous_scale="Reds"),
            use_container_width=True
        )

    # ---- Tab 3 ----
    with tab3:
        st.subheader("Validation Summary")
        col1, col2 = st.columns([1.2, 1])
        with col1:
            fig = px.pie(validation_data, names="Outcome", values="Cases", color="Outcome",
                         color_discrete_map={
                             "Confirmed Fraud": "#ef4444",
                             "Rejected (Legitimate)": "#22c55e",
                             "Escalated": "#f97316",
                             "Pending": "#a855f7",
                         })
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            total_cases = validation_data["Cases"].sum()
            for _, row in validation_data.iterrows():
                percent = (row["Cases"] / total_cases) * 100
                st.markdown(
                    f"""
                    <div style='margin-bottom:12px'>
                        <strong>{row["Outcome"]}</strong>
                        <div style='background-color:#e5e7eb;border-radius:8px;height:20px;overflow:hidden;margin-top:6px;'>
                            <div style='width:{percent}%;background-color:{row["Color"]};height:100%;'></div>
                        </div>
                        <div style='font-size:14px;margin-top:4px;color:gray'>
                            {row["Cases"]} cases ({percent:.1f}%)
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # ---- Tab 4 ----
    with tab4:
        st.subheader("SHAP Feature Importance")
        st.plotly_chart(
            px.bar(shap_data, x="Feature", y="SHAP Value", color="SHAP Value",
                   color_continuous_scale=["#3b82f6", "#ef4444"],
                   title="Top Features Affecting Fraud Predictions"),
            use_container_width=True
        )

    # ---- Tab 5 ----
    with tab5:
        st.subheader("NLP Keyword Analysis")
        st.dataframe(nlp_keywords, use_container_width=True)
        st.warning("🧠 These keywords often indicate potential fraud risk.")