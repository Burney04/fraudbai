import streamlit as st

def show():
    # --------------------------
    # PAGE HEADER
    # --------------------------
    st.title("🕵️ Case Inspection")
    st.markdown("**Inspect what is to be expected**")

    # --------------------------
    # MOCK CASE DATA
    # --------------------------
    mock_case = {
        "id": "FR-2025-0842",
        "card_number": "**** **** **** 7834",
        "bank": "Maybank",
        "amount": "RM 8,500.00",
        "merchant": "TechMart Electronics",
        "location": "Johor Bahru, Johor",
        "previous_location": "Kuala Lumpur, Selangor",
        "distance": "320 km",
        "time": "3:47 AM",
        "date": "Oct 12, 2025",
        "status": "Flagged - High Risk",
        "risk_score": 0.92,
        "complaint_text": (
            "Customer received SMS about urgent transfer required to verify account "
            "due to suspicious activity detected. Transaction occurred at unusual time "
            "with immediate action needed to prevent account locked."
        ),
        "structured_features": [
            {"label": "Transaction Amount", "value": "RM 8,500.00", "risk": "high"},
            {"label": "Time of Day", "value": "3:47 AM (Off-hours)", "risk": "high"},
            {"label": "Location Change", "value": "520km in 2 hours", "risk": "high"},
            {"label": "Merchant Category", "value": "Electronics (High-value)", "risk": "medium"},
            {"label": "Card Age", "value": "2.3 years", "risk": "low"},
            {"label": "Previous Transactions", "value": "523 transactions", "risk": "low"},
        ],
    }

    # --------------------------
    # HELPER FUNCTIONS
    # --------------------------
    def render_nlp_analysis(complaint_text):
        st.subheader("🧠 NLP Analysis")
        st.write("Extracted insights from complaint text:")
        st.info(complaint_text[:250] + "...")

    def render_shap_explainability(prediction_score, case_id):
        st.subheader("📊 SHAP Explainability")
        st.write(f"Model explainability for **{case_id}**")
        st.progress(prediction_score)

    # --------------------------
    # CASE SELECTION
    # --------------------------
    st.subheader("Case Selection")
    selected_case = st.selectbox(
        "Select a case",
        ["FR-2025-0842 - High Risk", "FR-2025-0841 - Medium Risk", "FR-2025-0840 - High Risk"],
        index=0,
    )
    st.divider()

    # --------------------------
    # CASE OVERVIEW
    # --------------------------
    with st.container():
        st.markdown("### 🚨 Case Overview")
        st.markdown(
            f"**Case ID:** {mock_case['id']} &nbsp; | &nbsp; "
            f"**Date:** {mock_case['date']} at {mock_case['time']}  \n"
            f"**Risk Score:** 🟥 **{mock_case['risk_score']*100:.0f}% (High Risk)**"
        )

        col1, col2, col3 = st.columns(3)
        with col1:
            st.write("**💳 Card Number:**", mock_case["card_number"])
            st.write("**🏦 Bank:**", mock_case["bank"])
        with col2:
            st.write("**🛒 Merchant:**", mock_case["merchant"])
            st.write(
                "**📍 Location Change:**",
                f"{mock_case['previous_location']} ➜ {mock_case['location']}",
            )
        with col3:
            st.write("**🕓 Transaction Time:**", f"{mock_case['time']} (Off-hours)")
            st.write("**💰 Amount:**", mock_case["amount"])

    st.divider()

    # --------------------------
    # STRUCTURED FEATURES
    # --------------------------
    st.subheader("📋 Structured Features")
    cols = st.columns(3)
    for i, feature in enumerate(mock_case["structured_features"]):
        col = cols[i % 3]
        with col:
            color = (
                "red" if feature["risk"] == "high"
                else "orange" if feature["risk"] == "medium"
                else "green"
            )
            st.markdown(
                f"<div style='border:1px solid #ddd;padding:10px;border-radius:8px;"
                f"background-color:{color}10;'>"
                f"<b>{feature['label']}</b><br>"
                f"{feature['value']}<br>"
                f"<span style='color:{color};font-weight:bold;text-transform:capitalize;'>"
                f"{feature['risk']}</span></div>",
                unsafe_allow_html=True,
            )

    st.divider()

    # --------------------------
    # EXPLAINABILITY SECTION
    # --------------------------
    col_nlp, col_shap = st.columns(2)
    with col_nlp:
        render_nlp_analysis(mock_case["complaint_text"])
    with col_shap:
        render_shap_explainability(mock_case["risk_score"], mock_case["id"])

    st.divider()

    # --------------------------
    # ACTION BUTTONS
    # --------------------------
    col1, col2 = st.columns([3, 1])
    with col2:
        st.button("📄 Export Report")
        if st.button("🚀 Send to Validation Queue"):
            st.success("Case sent to validation queue ✅")