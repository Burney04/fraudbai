import streamlit as st
import plotly.express as px
import pandas as pd
from FraudShield.utils.supabase_client import supabase
from datetime import datetime
import time
import re
from io import BytesIO
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

def render_reports():
    st.title("📊 Fraud Detection Reports")
    st.caption("Comprehensive fraud analytics with explainability insights")
    st.divider()

    # --- PDF Generation Function ---
    def generate_pdf_report():
        """Generate a PDF report with all charts and data."""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
        styles = getSampleStyleSheet()
        elements = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1f2937'),
            spaceAfter=30
        )
        elements.append(Paragraph("Fraud Detection Report", title_style))
        elements.append(Spacer(1, 0.2 * inch))
        
        # Date and time
        date_style = ParagraphStyle(
            'DateStyle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.gray
        )
        elements.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", date_style))
        elements.append(Spacer(1, 0.3 * inch))
        
        # KPI Summary
        elements.append(Paragraph("Key Performance Indicators", styles['Heading2']))
        elements.append(Spacer(1, 0.1 * inch))
        
        # Create KPI table
        kpi_data = [["Metric", "Value", "Change"]]
        for stat in stats:
            kpi_data.append([stat["title"], stat["value"], f"{stat['change']}%"])
        
        kpi_table = Table(kpi_data)
        kpi_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3B82F6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
        ]))
        elements.append(kpi_table)
        elements.append(Spacer(1, 0.3 * inch))
        
        # Fraud Trends
        elements.append(Paragraph("Fraud Detection Trends", styles['Heading2']))
        elements.append(Spacer(1, 0.1 * inch))
        
        # Create fraud trend table
        trend_data = [["Month", "Detected", "Prevented", "Saved (MYR)"]]
        for _, row in fraud_trend.iterrows():
            trend_data.append([row["Month"], row["Detected"], row["Prevented"], f"RM {row['Saved (MYR)']:,}"])
        
        trend_table = Table(trend_data)
        trend_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3B82F6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
        ]))
        elements.append(trend_table)
        elements.append(Spacer(1, 0.3 * inch))
        
        # Geographic Distribution
        elements.append(Paragraph("Geographic Fraud Distribution", styles['Heading2']))
        elements.append(Spacer(1, 0.1 * inch))
        
        geo_data_list = [["Region", "Cases"]]
        for _, row in geo_data.iterrows():
            geo_data_list.append([row["Region"], row["Cases"]])
        
        geo_table = Table(geo_data_list)
        geo_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3B82F6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
        ]))
        elements.append(geo_table)
        elements.append(Spacer(1, 0.3 * inch))
        
        # Validation Summary
        elements.append(Paragraph("Validation Summary", styles['Heading2']))
        elements.append(Spacer(1, 0.1 * inch))
        
        validation_data_list = [["Outcome", "Cases", "Percentage"]]
        total_validation_cases = validation_data["Cases"].sum()
        for _, row in validation_data.iterrows():
            percentage = (row["Cases"] / total_validation_cases) * 100
            validation_data_list.append([row["Outcome"], row["Cases"], f"{percentage:.1f}%"])
        
        validation_table = Table(validation_data_list)
        validation_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3B82F6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
        ]))
        elements.append(validation_table)
        elements.append(Spacer(1, 0.3 * inch))
        
        # SHAP Feature Importance
        elements.append(Paragraph("SHAP Feature Importance", styles['Heading2']))
        elements.append(Spacer(1, 0.1 * inch))
        
        shap_data_list = [["Feature", "SHAP Value"]]
        for _, row in shap_data.iterrows():
            shap_data_list.append([row["Feature"], f"{row['SHAP Value']:.3f}"])
        
        shap_table = Table(shap_data_list)
        shap_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3B82F6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
        ]))
        elements.append(shap_table)
        elements.append(Spacer(1, 0.3 * inch))
        
        # NLP Keywords
        elements.append(Paragraph("NLP Keyword Analysis", styles['Heading2']))
        elements.append(Spacer(1, 0.1 * inch))
        
        nlp_data_list = [["Keyword", "Frequency", "Risk Increase (%)", "SHAP Contribution"]]
        for _, row in nlp_keywords.iterrows():
            nlp_data_list.append([row["Keyword"], row["Frequency"], f"{row['Risk Increase (%)']}%", f"{row['SHAP Contribution']:.2f}"])
        
        nlp_table = Table(nlp_data_list)
        nlp_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3B82F6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
        ]))
        elements.append(nlp_table)
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer

    # --- Track notification state ---
    if 'limit_version' not in st.session_state:
        st.session_state.limit_version = 1
    if 'notification_shown_for_version' not in st.session_state:
        st.session_state.notification_shown_for_version = None

    # --- Define the display limit - CHANGE THIS NUMBER TO TEST ---
    # Change this from 1000 to 1001 to see the notification
    CURRENT_LIMIT = 1000  # <-- CHANGE THIS TO 1001 TO TEST

    # Check if the limit has been increased (version tracking)
    if CURRENT_LIMIT > st.session_state.limit_version:
        # Show toast notification
        new_cases = CURRENT_LIMIT - st.session_state.limit_version
        st.toast(f"🔔 {new_cases} new case(s) has been updated into View Alert!", icon="📊")
        # Update the version to prevent showing again
        st.session_state.limit_version = CURRENT_LIMIT

    # --- Load Data for View Alert from fraud_cases table ---
    @st.cache_data(ttl=60)
    def load_alert_data(limit):
        """Load fraud cases data for View Alert tab."""
        try:
            response = supabase.table("fraud_cases") \
                .select("case_id, amount_formatted, risk_display, transaction_date, created_at") \
                .limit(limit) \
                .execute()
            
            if response.data:
                df = pd.DataFrame(response.data)
                # Sort by case_id numerically to show smaller IDs first
                if 'case_id' in df.columns:
                    df['case_id_num'] = df['case_id'].str.extract(r'(\d+)$').astype(int)
                    df = df.sort_values('case_id_num').drop('case_id_num', axis=1)
                return df
            else:
                return pd.DataFrame()
        except Exception as e:
            st.error(f"Error loading alert data: {e}")
            return pd.DataFrame()
    
    def extract_risk_score(risk_display):
        """Extract numeric risk score from risk display."""
        try:
            if pd.isna(risk_display):
                return 0.5
            
            risk_str = str(risk_display)
            
            # Try to find percentage format (e.g., "90%")
            if '%' in risk_str:
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
    
    def get_risk_level(risk_display):
        """Get risk level category from risk display."""
        try:
            if pd.isna(risk_display):
                return 'Unknown'
            
            risk_str = str(risk_display).lower()
            
            # First try to extract numeric score
            risk_score = extract_risk_score(risk_display)
            
            # Determine risk level based on numeric score
            if risk_score >= 0.70:
                return 'High'
            elif risk_score >= 0.40:
                return 'Medium'
            elif risk_score > 0:
                return 'Low'
            
            # Fallback to text matching
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

    # --- Load alert data ---
    alert_df = load_alert_data(limit=CURRENT_LIMIT)

    # --- Get total count for info display ---
    @st.cache_data(ttl=60)
    def get_total_case_count():
        """Get total number of cases in the database."""
        try:
            response = supabase.table("fraud_cases") \
                .select("case_id", count="exact") \
                .execute()
            return response.count if hasattr(response, 'count') else 0
        except Exception as e:
            return 0
    
    total_cases_in_db = get_total_case_count()

    # --- KPI Data (moved inside Fraud Trends tab) ---
    stats = [
        {"title": "Total Transactions", "value": "52,340", "change": 15.3},
        {"title": "Flagged Cases", "value": 142, "change": -8.2},
        {"title": "Validated Cases", "value": 98, "change": 12.5},
        {"title": "Amount Saved (RM)", "value": "932K", "change": 15.0},
        {"title": "Threats Detected", "value": 337, "change": 8.0},
    ]

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

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🚨 View Alert", "📈 Fraud Trends", "🗺️ Geography", "✅ Validation", "🎯 SHAP Summary", "🧠 NLP Keywords"
    ])

    # ---- Tab 1: View Alert ----
    with tab1:
        st.subheader("Alert Queue")
        
        if not alert_df.empty:
            # Process the data to create the required columns
            alert_data = []
            for _, row in alert_df.iterrows():
                risk_score = extract_risk_score(row.get('risk_display', 'N/A'))
                risk_level = get_risk_level(row.get('risk_display', 'N/A'))
                fraud_score_percentage = f"{int(risk_score * 100)}%"
                
                alert_data.append({
                    "transaction_id": row.get('case_id', 'N/A'),
                    "amount": row.get('amount_formatted', 'N/A'),
                    "fraud_score": fraud_score_percentage,
                    "risk_level": risk_level,
                    "timestamp": row.get('transaction_date', row.get('created_at', 'N/A')),
                    "Key reasons": "N/A",
                })
            
            df_alerts = pd.DataFrame(alert_data)
            
            # Calculate counts
            total_alerts = len(alert_data)
            high_risk_count = len([a for a in alert_data if a['risk_level'] == 'High'])
            medium_risk_count = len([a for a in alert_data if a['risk_level'] == 'Medium'])
            low_risk_count = len([a for a in alert_data if a['risk_level'] == 'Low'])
            unknown_risk_count = len([a for a in alert_data if a['risk_level'] == 'Unknown'])
            
            # Alert Summary
            # Display risk breakdown in columns
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("🔴 High Risk", high_risk_count, delta=f"{high_risk_count/total_alerts*100:.1f}%" if total_alerts > 0 else "0%")
            with col2:
                st.metric("🟠 Medium Risk", medium_risk_count, delta=f"{medium_risk_count/total_alerts*100:.1f}%" if total_alerts > 0 else "0%")
            with col3:
                st.metric("🟢 Low Risk", low_risk_count, delta=f"{low_risk_count/total_alerts*100:.1f}%" if total_alerts > 0 else "0%")
            with col4:
                st.metric("📊 Total Displayed", total_alerts)
            
            st.divider()
            
             # Show total cases info with refresh button inline
            if total_cases_in_db > CURRENT_LIMIT:
                # Create two columns for the info message and refresh button
                info_col, refresh_col = st.columns([5, 1])
                with info_col:
                    st.info(f"ℹ️ Showing first {CURRENT_LIMIT} cases. Total cases in database: {total_cases_in_db:,}. New cases beyond the first {CURRENT_LIMIT} will appear here as they move into the top {CURRENT_LIMIT}.")
                with refresh_col:
                    if st.button("🔄 Refresh", key="refresh_alerts_btn", use_container_width=True):
                        st.cache_data.clear()
                        st.rerun()
            else:
                # Show just the refresh button if no info message
                col1, col2, col3 = st.columns([4, 1, 4])
                with col2:
                    if st.button("🔄 Refresh Alerts", key="refresh_alerts_btn_solo", use_container_width=True):
                        st.cache_data.clear()
                        st.rerun()

            # Display the table
            st.dataframe(
                df_alerts,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "transaction_id": st.column_config.TextColumn("Transaction ID", width="medium"),
                    "amount": st.column_config.TextColumn("Amount", width="small"),
                    "fraud_score": st.column_config.TextColumn("Fraud Score", width="small"),
                    "risk_level": st.column_config.TextColumn("Risk Level", width="small"),
                    "timestamp": st.column_config.DatetimeColumn("Timestamp", width="medium"),
                    "Key reasons": st.column_config.TextColumn("Key Reasons", width="large"),
                }
            )
            
            # Export buttons for alerts
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("📥 Export Alerts to CSV", use_container_width=True, key="export_alerts_btn"):
                    csv = df_alerts.to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name=f"fraud_alerts_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        key="export_alerts_download"
                    )
        else:
            st.info("📭 No alert data available at this time.")

    # ---- Tab 2: Fraud Trends (with KPI metrics now inside) ----
    with tab2:
        # Display KPI metrics at the top of the Fraud Trends tab
        st.subheader("Key Performance Indicators")
        
        # Create 5 columns for the 5 metrics
        cols = st.columns(5)
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
        
        # Original Fraud Trends content
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
            st.plotly_chart(fig, use_container_width=True, key="fraud_trend_chart")
        with col2:
            st.subheader("💰 Amount Saved (MYR)")
            st.plotly_chart(
                px.area(fraud_trend, x="Month", y="Saved (MYR)", title="Total Amount Saved", color_discrete_sequence=["#22c55e"]),
                use_container_width=True,
                key="saved_amount_chart"
            )

    # ---- Tab 3: Geography ----
    with tab3:
        st.subheader("Geographic Fraud Trends")
        st.plotly_chart(
            px.bar(geo_data, x="Region", y="Cases", color="Cases", title="Fraud Cases by Region", color_continuous_scale="Reds"),
            use_container_width=True,
            key="geo_chart"
        )

    # ---- Tab 4: Validation ----
    with tab4:
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
            st.plotly_chart(fig, use_container_width=True, key="validation_pie_chart")
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

    # ---- Tab 5: SHAP Summary ----
    with tab5:
        st.subheader("SHAP Feature Importance")
        st.plotly_chart(
            px.bar(shap_data, x="Feature", y="SHAP Value", color="SHAP Value",
                   color_continuous_scale=["#3b82f6", "#ef4444"],
                   title="Top Features Affecting Fraud Predictions"),
            use_container_width=True,
            key="shap_chart"
        )

    # ---- Tab 6: NLP Keywords ----
    with tab6:
        st.subheader("NLP Keyword Analysis")
        st.dataframe(nlp_keywords, use_container_width=True)
        st.warning("🧠 These keywords often indicate potential fraud risk.")
    
    # ---- Footer Controls (moved to bottom) ----
    st.divider()
    
    # Period selector
    period_value = st.selectbox("Select Period", ["1 month", "3 months", "6 months", "1 year"], index=2, key="period_select_bottom")
    
    # Display the current period message
    st.write(f"Currently viewing **{period_value}** trend.")
    
    # Export buttons (CSV and PDF)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("📊 Export Report as CSV", use_container_width=True, key="export_csv_btn"):
            # Create a comprehensive CSV with all data
            csv_data = []
            
            # Add KPI data
            for stat in stats:
                csv_data.append({"Section": "KPIs", "Metric": stat["title"], "Value": stat["value"], "Change": f"{stat['change']}%"})
            
            # Add fraud trend data
            for _, row in fraud_trend.iterrows():
                csv_data.append({"Section": "Fraud Trends", "Metric": f"{row['Month']} - Detected", "Value": row["Detected"], "Change": ""})
                csv_data.append({"Section": "Fraud Trends", "Metric": f"{row['Month']} - Prevented", "Value": row["Prevented"], "Change": ""})
                csv_data.append({"Section": "Fraud Trends", "Metric": f"{row['Month']} - Saved", "Value": f"RM {row['Saved (MYR)']:,}", "Change": ""})
            
            # Add geographic data
            for _, row in geo_data.iterrows():
                csv_data.append({"Section": "Geography", "Metric": row["Region"], "Value": row["Cases"], "Change": ""})
            
            # Add validation data
            for _, row in validation_data.iterrows():
                csv_data.append({"Section": "Validation", "Metric": row["Outcome"], "Value": row["Cases"], "Change": ""})
            
            # Add SHAP data
            for _, row in shap_data.iterrows():
                csv_data.append({"Section": "SHAP Analysis", "Metric": row["Feature"], "Value": row["SHAP Value"], "Change": ""})
            
            # Add NLP keywords
            for _, row in nlp_keywords.iterrows():
                csv_data.append({"Section": "NLP Keywords", "Metric": row["Keyword"], "Value": row["Frequency"], "Change": f"{row['Risk Increase (%)']}% increase"})
            
            export_df = pd.DataFrame(csv_data)
            csv = export_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"fraud_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                key="download_csv"
            )
    
    with col2:
        if st.button("📄 Export Report as PDF", use_container_width=True, key="export_pdf_btn"):
            with st.spinner("Generating PDF report..."):
                pdf_buffer = generate_pdf_report()
                st.download_button(
                    label="Download PDF",
                    data=pdf_buffer,
                    file_name=f"fraud_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf",
                    key="download_pdf"
                )