import streamlit as st
import plotly.express as px
import pandas as pd
from FraudShield.utils.supabase_client import supabase
from datetime import datetime, timedelta
import time
import re
from io import BytesIO
from reportlab.lib.pagesizes import letter, landscape, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

def render_reports():
    st.title("📊 Fraud Detection Reports")
    st.caption("Comprehensive fraud analytics with explainability insights")
    st.divider()

    # --- ENHANCED PDF Generation Function ---
    def generate_pdf_report():
        """Generate an enhanced PDF report with all analytics and insights."""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1f2937'),
            spaceAfter=20
        )
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#3B82F6'),
            spaceAfter=12,
            spaceBefore=10
        )
        subheading_style = ParagraphStyle(
            'CustomSubheading',
            parent=styles['Heading3'],
            fontSize=13,
            textColor=colors.HexColor('#4B5563'),
            spaceAfter=8
        )
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#374151'),
            spaceAfter=6
        )
        insight_style = ParagraphStyle(
            'InsightStyle',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#6B7280'),
            leftIndent=20,
            spaceAfter=4
        )
        
        # ============================================================
        # REPORT HEADER
        # ============================================================
        elements.append(Paragraph("FraudbAI Intelligence Report", title_style))
        elements.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", normal_style))
        elements.append(Paragraph(f"Reporting Period: {period_value}", normal_style))
        elements.append(Paragraph(f"Total Fraud Cases in Database: {total_cases_in_db:,}", normal_style))
        elements.append(Paragraph(f"Cases Analyzed in Report: {len(alert_df):,} (starting from Case 4000)", normal_style))
        elements.append(Spacer(1, 0.3 * inch))
        
        # ============================================================
        # EXECUTIVE SUMMARY
        # ============================================================
        elements.append(Paragraph("Executive Summary", heading_style))
        
        # Calculate executive summary metrics
        if not alert_df.empty:
            amounts = []
            for _, row in alert_df.iterrows():
                amount_str = str(row.get('amount_formatted', 'RM 0'))
                amount_num = re.sub(r'[^\d.]', '', amount_str.replace('RM', '').replace(',', ''))
                try:
                    amounts.append(float(amount_num))
                except:
                    amounts.append(0)
            
            total_amount = sum(amounts)
            avg_amount = total_amount / len(amounts) if amounts else 0
            max_amount = max(amounts) if amounts else 0
            min_amount = min(amounts) if amounts else 0
            
            risk_scores = []
            for _, row in alert_df.iterrows():
                score = extract_risk_score(row.get('risk_display', 'N/A'))
                risk_scores.append(score)
            
            avg_risk_score = sum(risk_scores) / len(risk_scores) if risk_scores else 0
            
            confirmed_fraud = validation_data[validation_data['Outcome'] == 'Confirmed Fraud']['Cases'].values[0] if not validation_data.empty else 98
            legitimate = validation_data[validation_data['Outcome'] == 'Rejected (Legitimate)']['Cases'].values[0] if not validation_data.empty else 127
        else:
            total_amount = avg_amount = max_amount = min_amount = avg_risk_score = 0
            confirmed_fraud = 98
            legitimate = 127
        
        exec_data = [
            ["Metric", "Value", "Key Insight"],
            ["Total Transaction Volume", f"RM {total_amount:,.2f}", "Total value of analyzed transactions"],
            ["Average Transaction", f"RM {avg_amount:,.2f}", "Typical fraud target size"],
            ["Largest Transaction", f"RM {max_amount:,.2f}", "Highest value case flagged"],
            ["Average Risk Score", f"{avg_risk_score*100:.1f}%", "Mean risk across all cases"],
            ["High Risk Cases", f"{high_risk_count} ({high_risk_count/len(alert_df)*100:.1f}%)" if not alert_df.empty else "0", "Require immediate attention"],
            ["Medium Risk Cases", f"{medium_risk_count} ({medium_risk_count/len(alert_df)*100:.1f}%)" if not alert_df.empty else "0", "Require monitoring"],
            ["Low Risk Cases", f"{low_risk_count} ({low_risk_count/len(alert_df)*100:.1f}%)" if not alert_df.empty else "0", "Lower priority"],
            ["Confirmed Fraud", f"{confirmed_fraud}", "Validated as actual fraud"],
            ["Legitimate Cases", f"{legitimate}", "Validated as legitimate"],
            ["Fraud Detection Rate", f"{(confirmed_fraud/(confirmed_fraud+legitimate)*100):.1f}%" if (confirmed_fraud+legitimate) > 0 else "0%", "Cases confirmed as fraud"],
            ["Est. Amount Saved", f"RM {total_amount * (confirmed_fraud/(confirmed_fraud+legitimate+escalated)):,.2f}" if (confirmed_fraud+legitimate+escalated) > 0 else "RM 0", "Estimated fraud prevented"]
        ]
        
        exec_table = Table(exec_data, colWidths=[2.5*inch, 1.5*inch, 2.5*inch])
        exec_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3B82F6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F3F4F6')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D1D5DB')),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(exec_table)
        elements.append(Spacer(1, 0.3 * inch))
        
        # Key Findings
        elements.append(Paragraph("Key Findings", subheading_style))
        elements.append(Paragraph(f"• {high_risk_count} high-risk cases require immediate review", insight_style))
        elements.append(Paragraph(f"• Fraud detection rate is {(confirmed_fraud/(confirmed_fraud+legitimate)*100):.1f}%", insight_style))
        elements.append(Paragraph(f"• Average transaction amount of RM {avg_amount:,.2f} indicates typical fraud target", insight_style))
        elements.append(Spacer(1, 0.2 * inch))
        
        # ============================================================
        # KPI SUMMARY
        # ============================================================
        elements.append(Paragraph("Key Performance Indicators", heading_style))
        
        kpi_data = [["Metric", "Value", "Change", "Status"]]
        for stat in stats:
            status = "✅ Healthy" if stat["change"] > 0 else "⚠️ Monitor" if stat["change"] < -5 else "➖ Stable"
            kpi_data.append([stat["title"], stat["value"], f"{stat['change']}%", status])
        
        kpi_table = Table(kpi_data, colWidths=[2*inch, 1.2*inch, 1*inch, 1.2*inch])
        kpi_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3B82F6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F3F4F6')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D1D5DB')),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
        ]))
        elements.append(kpi_table)
        elements.append(Spacer(1, 0.3 * inch))
        
        # ============================================================
        # FRAUD DETECTION TRENDS
        # ============================================================
        elements.append(Paragraph("Fraud Detection Trends", heading_style))
        elements.append(Paragraph("Monthly analysis of fraud detection and prevention activities", normal_style))
        elements.append(Spacer(1, 0.1 * inch))
        
        trend_data = [["Month", "Detected", "Prevented", "Saved (MYR)", "Prevention Rate"]]
        for _, row in fraud_trend.iterrows():
            prevention_rate = (row["Prevented"] / row["Detected"] * 100) if row["Detected"] > 0 else 0
            trend_data.append([
                row["Month"], 
                row["Detected"], 
                row["Prevented"], 
                f"RM {row['Saved (MYR)']:,}",
                f"{prevention_rate:.1f}%"
            ])
        
        trend_table = Table(trend_data, colWidths=[0.8*inch, 1*inch, 1*inch, 1.3*inch, 1.2*inch])
        trend_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3B82F6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F3F4F6')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D1D5DB')),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
        ]))
        elements.append(trend_table)
        
        avg_prevention = (fraud_trend['Prevented'].sum() / fraud_trend['Detected'].sum() * 100)
        elements.append(Paragraph(f"Insight: Prevention rate averaged {avg_prevention:.1f}% over the period", insight_style))
        elements.append(Spacer(1, 0.3 * inch))
        
        # ============================================================
        # GEOGRAPHIC DISTRIBUTION
        # ============================================================
        elements.append(Paragraph("Geographic Fraud Distribution", heading_style))
        
        total_geo_cases = geo_data["Cases"].sum()
        geo_export_data = [["Region", "Cases", "Percentage", "Risk Level"]]
        risk_levels = ["High", "Medium", "Medium", "Low", "Low"]
        for i, (_, row) in enumerate(geo_data.iterrows()):
            percentage = (row["Cases"] / total_geo_cases * 100)
            geo_export_data.append([
                row["Region"], 
                row["Cases"], 
                f"{percentage:.1f}%",
                risk_levels[i] if i < len(risk_levels) else "Medium"
            ])
        
        geo_table = Table(geo_export_data, colWidths=[1.5*inch, 1*inch, 1.2*inch, 1*inch])
        geo_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3B82F6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F3F4F6')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D1D5DB')),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
        ]))
        elements.append(geo_table)
        
        kl_pct = (geo_data[geo_data['Region']=='Kuala Lumpur']['Cases'].values[0]/total_geo_cases*100) if total_geo_cases > 0 else 0
        elements.append(Paragraph(f"Insight: Kuala Lumpur accounts for {kl_pct:.1f}% of all fraud cases", insight_style))
        elements.append(Spacer(1, 0.3 * inch))
        
        # ============================================================
        # VALIDATION SUMMARY
        # ============================================================
        elements.append(Paragraph("Validation Summary", heading_style))
        
        validation_export_data = [["Outcome", "Cases", "Percentage", "Action Required"]]
        total_validated = validation_data["Cases"].sum()
        actions = ["Investigate and report", "No action needed", "Escalate to senior analyst", "Complete validation"]
        for i, (_, row) in enumerate(validation_data.iterrows()):
            percentage = (row["Cases"] / total_validated * 100)
            validation_export_data.append([
                row["Outcome"], 
                row["Cases"], 
                f"{percentage:.1f}%",
                actions[i] if i < len(actions) else "Review"
            ])
        
        validation_table = Table(validation_export_data, colWidths=[1.8*inch, 1*inch, 1.2*inch, 1.8*inch])
        validation_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3B82F6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F3F4F6')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D1D5DB')),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
        ]))
        elements.append(validation_table)
        elements.append(Spacer(1, 0.3 * inch))
        
        # ============================================================
        # SHAP FEATURE IMPORTANCE
        # ============================================================
        elements.append(Paragraph("SHAP Feature Importance Analysis", heading_style))
        elements.append(Paragraph("Model explainability - factors influencing fraud predictions", normal_style))
        elements.append(Spacer(1, 0.1 * inch))
        
        shap_export_data = [["Feature", "SHAP Value", "Impact", "Interpretation"]]
        interpretations = [
            "Large transactions significantly increase fraud risk",
            "Transactions outside business hours are highly suspicious",
            "Rapid location changes strongly indicate potential fraud",
            "Urgency keywords correlate with fraudulent activity",
            "Established customers show lower fraud risk (negative impact)"
        ]
        for i, (_, row) in enumerate(shap_data.iterrows()):
            impact = "Strong Positive" if row["SHAP Value"] > 0.3 else "Moderate Positive" if row["SHAP Value"] > 0.1 else "Negative"
            shap_export_data.append([
                row["Feature"], 
                f"{row['SHAP Value']:.3f}", 
                impact,
                interpretations[i] if i < len(interpretations) else "N/A"
            ])
        
        shap_table = Table(shap_export_data, colWidths=[2*inch, 1*inch, 1.2*inch, 2.5*inch])
        shap_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3B82F6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F3F4F6')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D1D5DB')),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(shap_table)
        elements.append(Spacer(1, 0.3 * inch))
        
        # ============================================================
        # NLP KEYWORD ANALYSIS
        # ============================================================
        elements.append(Paragraph("NLP Keyword Intelligence", heading_style))
        elements.append(Paragraph("Keywords strongly associated with fraudulent transactions", normal_style))
        elements.append(Spacer(1, 0.1 * inch))
        
        nlp_export_data = [["Keyword", "Frequency", "Risk Increase", "SHAP Contrib.", "Priority"]]
        for _, row in nlp_keywords.iterrows():
            priority = "🔴 Critical" if row["Risk Increase (%)"] > 20 else "🟠 High" if row["Risk Increase (%)"] > 15 else "🟡 Medium"
            nlp_export_data.append([
                row["Keyword"], 
                row["Frequency"], 
                f"{row['Risk Increase (%)']}%",
                f"{row['SHAP Contribution']:.2f}",
                priority
            ])
        
        nlp_table = Table(nlp_export_data, colWidths=[1.5*inch, 1*inch, 1.2*inch, 1.2*inch, 1.2*inch])
        nlp_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3B82F6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F3F4F6')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D1D5DB')),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
        ]))
        elements.append(nlp_table)
        elements.append(Paragraph("Key Finding: 'urgent transfer' and 'verify account' are the strongest fraud indicators", insight_style))
        elements.append(Spacer(1, 0.3 * inch))
        
        # ============================================================
        # RECOMMENDATIONS AND ACTION ITEMS
        # ============================================================
        elements.append(PageBreak())
        elements.append(Paragraph("Recommendations & Action Items", heading_style))
        elements.append(Spacer(1, 0.1 * inch))
        
        rec_data = [["Priority", "Category", "Recommendation", "Expected Impact", "Timeline"]]
        recommendations = [
            ["High", "Risk Monitoring", f"Immediately review {high_risk_count} high-risk cases", "Prevent potential fraud losses", "Immediate"],
            ["High", "Geographic", "Implement additional verification for Kuala Lumpur region", "Reduce regional fraud by 15-20%", "1 Week"],
            ["Medium", "Validation", f"Escalate {escalated} pending cases for senior review", "Improve validation accuracy", "48 Hours"],
            ["Medium", "NLP", "Add 'urgent transfer' and 'verify account' to detection rules", "Increase detection rate by 5-10%", "2 Weeks"],
            ["Low", "Process", "Schedule weekly fraud pattern review meetings", "Continuous improvement", "Ongoing"]
        ]
        
        for rec in recommendations:
            rec_data.append(rec)
        
        rec_table = Table(rec_data, colWidths=[0.8*inch, 1.2*inch, 2*inch, 1.8*inch, 0.9*inch])
        rec_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#EF4444')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#FEF2F2')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#FCA5A5')),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(rec_table)
        elements.append(Spacer(1, 0.3 * inch))
        
        # ============================================================
        # REPORT FOOTER
        # ============================================================
        elements.append(Paragraph("---", normal_style))
        elements.append(Paragraph("Report Generated by: FraudShield AI Detection System", normal_style))
        elements.append(Paragraph("Contact: fraud-team@fraudshield.com", normal_style))
        elements.append(Paragraph(f"Next Report Scheduled: {(datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')}", normal_style))
        elements.append(Paragraph("CONFIDENTIAL - For Internal Use Only", insight_style))
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer

    # --- Track notification state ---
    if 'limit_version' not in st.session_state:
        st.session_state.limit_version = 1
    if 'notification_shown_for_version' not in st.session_state:
        st.session_state.notification_shown_for_version = None

    # --- Define the display limit ---
    CURRENT_LIMIT = 1000

    # Check if the limit has been increased (version tracking)
    if CURRENT_LIMIT > st.session_state.limit_version:
        new_cases = CURRENT_LIMIT - st.session_state.limit_version
        st.toast(f"🔔 {new_cases} new case(s) has been updated into View Alert!", icon="📊")
        st.session_state.limit_version = CURRENT_LIMIT

    # --- Load Data for View Alert from fraud_cases table ---
    @st.cache_data(ttl=60)
    def load_alert_data(limit):
        """Load fraud cases data for View Alert tab starting from case 4000."""
        try:
            response = supabase.table("fraud_cases") \
                .select("case_id, amount_formatted, risk_display, transaction_date, created_at") \
                .gte('case_id', 'FR-2025-4000') \
                .order('case_id', desc=False) \
                .limit(limit) \
                .execute()
            
            if response.data:
                df = pd.DataFrame(response.data)
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
            
            if '%' in risk_str:
                percentage_match = re.search(r'(\d+)%', risk_str)
                if percentage_match:
                    return int(percentage_match.group(1)) / 100
            
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
            risk_score = extract_risk_score(risk_display)
            
            if risk_score >= 0.70:
                return 'High'
            elif risk_score >= 0.40:
                return 'Medium'
            elif risk_score > 0:
                return 'Low'
            
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

    # --- KPI Data ---
    stats = [
        {"title": "Total Transactions", "value": "52,340", "change": 15.3},
        {"title": "Flagged Cases", "value": 142, "change": -8.2},
        {"title": "Validated Cases", "value": 98, "change": 12.5},
        {"title": "Amount Saved (RM)", "value": "932K", "change": 15.0},
        {"title": "Threats Detected", "value": 337, "change": 8.0},
    ]

    # --- Calculate risk counts for later use ---
    if not alert_df.empty:
        high_risk_count = len([a for a in alert_df.to_dict('records') if get_risk_level(a.get('risk_display', 'N/A')) == 'High'])
        medium_risk_count = len([a for a in alert_df.to_dict('records') if get_risk_level(a.get('risk_display', 'N/A')) == 'Medium'])
        low_risk_count = len([a for a in alert_df.to_dict('records') if get_risk_level(a.get('risk_display', 'N/A')) == 'Low'])
        escalated = validation_data[validation_data['Outcome'] == 'Escalated']['Cases'].values[0] if not validation_data.empty else 23
    else:
        high_risk_count = 0
        medium_risk_count = 0
        low_risk_count = 0
        escalated = 23

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
            total_alerts = len(alert_data)
            
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
            
            if total_cases_in_db > CURRENT_LIMIT:
                info_col, refresh_col = st.columns([5, 1])
                with info_col:
                    st.info(f"ℹ️ Showing first {CURRENT_LIMIT} cases starting from Case 4000 (ordered by Case ID ascending). Total cases in database: {total_cases_in_db:,}.")
                with refresh_col:
                    if st.button("🔄 Refresh", key="refresh_alerts_btn", use_container_width=True):
                        st.cache_data.clear()
                        st.rerun()
            else:
                col1, col2, col3 = st.columns([4, 1, 4])
                with col2:
                    if st.button("🔄 Refresh Alerts", key="refresh_alerts_btn_solo", use_container_width=True):
                        st.cache_data.clear()
                        st.rerun()

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

    # ---- Tab 2: Fraud Trends ----
    with tab2:
        st.subheader("Key Performance Indicators")
        
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
    
        # ---- Footer Controls ----
    st.divider()
    
    period_value = st.selectbox("Select Period", ["1 month", "3 months", "6 months", "1 year"], index=2, key="period_select_bottom")
    st.write(f"Currently viewing **{period_value}** trend.")
    
    # Export button (PDF only) - Single version with user email in filename
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("📄 Generate Report Insight (PDF)", use_container_width=True, type="primary", key="generate_pdf_report_btn"):
            with st.spinner("Generating enhanced PDF report with insights..."):
                pdf_buffer = generate_pdf_report()
                
                # Get user email from session state
                user_email = "unknown"
                if hasattr(st.session_state, 'user') and st.session_state.user:
                    if isinstance(st.session_state.user, dict):
                        user_email = st.session_state.user.get('email', 'unknown')
                    else:
                        user_email = getattr(st.session_state.user, 'email', 'unknown')
                
                # Extract username part only (before @) for cleaner filename
                username = user_email.split('@')[0] if '@' in user_email else user_email
                date_str = datetime.now().strftime('%Y%m%d')
                
                st.download_button(
                    label="📥 Download PDF Report",
                    data=pdf_buffer,
                    file_name=f"FraudbAI_Report_{date_str}_{username}.pdf",
                    mime="application/pdf",
                    key="download_pdf_final"
                )