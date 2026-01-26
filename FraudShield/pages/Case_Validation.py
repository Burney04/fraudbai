import streamlit as st

def show():
    # --- Mock Validation Queue Data ---
    validation_queue = [
        {"id": "FR-2025-0842", "amount": "RM 8,500", "risk_score": 0.78, "status": "pending", "merchant": "TechMart Electronics", "bank": "Maybank"},
        {"id": "FR-2025-0841", "amount": "RM 3,200", "risk_score": 0.68, "status": "pending", "merchant": "Online Store", "bank": "CIMB"},
        {"id": "FR-2025-0840", "amount": "RM 12,300", "risk_score": 0.85, "status": "pending", "merchant": "Luxury Goods", "bank": "Public Bank"},
        {"id": "FR-2025-0839", "amount": "RM 1,850", "risk_score": 0.52, "status": "pending", "merchant": "Restaurant", "bank": "RHB Bank"},
        {"id": "FR-2025-0838", "amount": "RM 4,200", "risk_score": 0.76, "status": "pending", "merchant": "Gadget Store", "bank": "Hong Leong"},
        {"id": "FR-2025-0837", "amount": "RM 6,700", "risk_score": 0.82, "status": "pending", "merchant": "Fashion Boutique", "bank": "AmBank"},
        {"id": "FR-2025-0836", "amount": "RM 2,900", "risk_score": 0.71, "status": "pending", "merchant": "Travel Agency", "bank": "Maybank"},
        {"id": "FR-2025-0835", "amount": "RM 5,400", "risk_score": 0.79, "status": "pending", "merchant": "Electronics Mall", "bank": "CIMB"},
    ]

    # --- Initialize Session State ---
    def init_state():
        """Initialize Streamlit session state variables."""
        if "cases" not in st.session_state:
            st.session_state.cases = validation_queue.copy()
        if "selected_case_id" not in st.session_state:
            st.session_state.selected_case_id = None
        if "notes" not in st.session_state:
            st.session_state.notes = ""

    # --- Helper Function ---
    def handle_validate(case_id, decision):
        """Update case status and provide user feedback."""
        for case_ in st.session_state.cases:
            if case_["id"] == case_id:
                case_["status"] = decision

        case_item = next((c for c in st.session_state.cases if c["id"] == case_id), None)
        messages = {
            "confirmed": f"✅ Case {case_id} confirmed as fraud. Customer will be notified.",
            "rejected": f"🟢 Case {case_id} marked as legitimate. No action needed.",
            "escalated": f"🟣 Case {case_id} escalated to supervisor for review.",
        }

        if case_item:
            st.toast(messages[decision], icon="💬")
            st.info(f"**Amount:** {case_item['amount']} | **Risk:** {case_item['risk_score']*100:.0f}%")

        # Reset form state
        st.session_state.notes = ""
        st.session_state.selected_case_id = None

    # --- Page Render Function ---
    def render():
        """Main UI for Validation Queue Page."""
        init_state()

        cases = st.session_state.cases
        selected_case_id = st.session_state.selected_case_id
        notes = st.session_state.notes

        pending_cases = [c for c in cases if c["status"] == "pending"]
        validated_cases = [c for c in cases if c["status"] != "pending"]

        # Identify possible retraining trigger
        high_risk_rejected = [
            c for c in validated_cases
            if c["status"] == "rejected" and 0.75 <= c["risk_score"] <= 0.85
        ]
        needs_retraining = len(high_risk_rejected) >= 3

        # --- Header ---
        st.title("🧾 Case Validation Queue")

        if needs_retraining:
            st.warning(
                f"⚠️ **Model Retraining Recommended:** {len(high_risk_rejected)} high-risk cases (75–85%) "
                "were marked legitimate. The model may require retraining."
            )

        st.info(
            "ℹ️ This queue shows only *ambiguous* cases (40–89% risk) requiring human validation. "
            "Cases ≥90% are automatically flagged as fraud."
        )

        # --- Stats Overview ---
        st.markdown("### 📊 Validation Summary")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Pending Validation", len(pending_cases))
        col2.metric("Confirmed Fraud", len([c for c in cases if c["status"] == "confirmed"]))
        col3.metric("Legitimate (Rejected)", len([c for c in cases if c["status"] == "rejected"]))
        col4.metric("Escalated", len([c for c in cases if c["status"] == "escalated"]))

        st.divider()

        # --- Layout: Queue + Validation Panel ---
        col_left, col_right = st.columns([2, 1])

        # --- Left Column: Pending Cases ---
        with col_left:
            st.subheader("🕵️ Ambiguous Cases")
            if not pending_cases:
                st.success("✅ All ambiguous cases have been validated!")
                st.caption("Cases ≥90% risk are auto-flagged as fraud.")
            else:
                for case_ in pending_cases:
                    color = (
                        "#FDE68A" if case_["risk_score"] >= 0.8
                        else "#FEF9C3" if case_["risk_score"] >= 0.6
                        else "#DBEAFE"
                    )
                    border = "#3B82F6" if selected_case_id == case_["id"] else "#E5E7EB"

                    if st.button(
                        f"{case_['id']} — {case_['merchant']} ({case_['bank']}) | 💰 {case_['amount']} | Risk {case_['risk_score']*100:.0f}%",
                        key=f"case_{case_['id']}",
                        help="Click to inspect this case",
                    ):
                        st.session_state.selected_case_id = case_["id"]

                    st.markdown(
                        f"<div style='background:{color};border:1px solid {border};border-radius:8px;"
                        f"padding:10px;margin-bottom:6px;'>"
                        f"<b>{case_['id']}</b> — {case_['merchant']} ({case_['bank']})<br>"
                        f"<b>Amount:</b> {case_['amount']} | <b>Risk:</b> {case_['risk_score']*100:.0f}%"
                        "</div>",
                        unsafe_allow_html=True,
                    )

        # --- Right Column: Validation Panel ---
        with col_right:
            st.subheader("🧩 Validation Decision")
            selected_case = next((c for c in cases if c["id"] == selected_case_id), None)

            if selected_case:
                st.write(f"### Selected Case: `{selected_case['id']}`")
                st.caption(f"{selected_case['merchant']} • {selected_case['bank']}")
                st.write(f"**Amount:** {selected_case['amount']} | **Risk:** {selected_case['risk_score']*100:.0f}%")

                st.text_area(
                    "💬 Feedback Notes",
                    value=notes,
                    placeholder="Add your feedback here...",
                    key="notes",
                )

                st.write("---")
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    if st.button("✅ Confirm Fraud", use_container_width=True):
                        handle_validate(selected_case["id"], "confirmed")
                with col_b:
                    if st.button("🟢 Legitimate", use_container_width=True):
                        handle_validate(selected_case["id"], "rejected")
                with col_c:
                    if st.button("🟣 Escalate", use_container_width=True):
                        handle_validate(selected_case["id"], "escalated")
            else:
                st.info("Select a case from the queue to validate.")

        st.divider()

        # --- Validated Cases History ---
        if validated_cases:
            st.subheader("📜 Recently Validated")
            for case_ in validated_cases:
                color = (
                    "green" if case_["status"] == "confirmed"
                    else "red" if case_["status"] == "rejected"
                    else "purple"
                )
                st.markdown(
                    f"<div style='background-color:{color}10;border:1px solid {color}30;"
                    f"padding:10px;border-radius:8px;margin-bottom:4px;'>"
                    f"**{case_['id']}** — {case_['amount']} | Risk: {case_['risk_score']*100:.0f}%<br>"
                    f"<b>Status:</b> <span style='color:{color};text-transform:capitalize;'>"
                    f"{case_['status']}</span>"
                    "</div>",
                    unsafe_allow_html=True,
                )
    render()