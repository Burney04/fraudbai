import streamlit as st
import pandas as pd
import altair as alt

def show():
    st.title("🧠 Model Insights Dashboard")
    st.markdown("**Monitoring model performance, drift, and prediction trends**")

    # --------------------------
    #  DATA DEFINITIONS
    # --------------------------
    performance_trend = pd.DataFrame([
        {"week": "Week 1", "f1": 0.89, "precision": 0.87, "recall": 0.91, "aucpr": 0.92},
        {"week": "Week 2", "f1": 0.90, "precision": 0.88, "recall": 0.92, "aucpr": 0.93},
        {"week": "Week 3", "f1": 0.91, "precision": 0.90, "recall": 0.92, "aucpr": 0.94},
        {"week": "Week 4", "f1": 0.92, "precision": 0.93, "recall": 0.91, "aucpr": 0.945},
    ])

    shap_drift = pd.DataFrame([
        {"feature": "Transaction Amount", "week1": 0.42, "week4": 0.38, "drift": -0.04, "status": "stable"},
        {"feature": "Time of Day", "week1": 0.35, "week4": 0.32, "drift": -0.03, "status": "stable"},
        {"feature": "Location Change", "week1": 0.28, "week4": 0.29, "drift": 0.01, "status": "stable"},
        {"feature": "NLP Keywords", "week1": 0.21, "week4": 0.24, "drift": 0.03, "status": "increasing"},
        {"feature": "Merchant Category", "week1": 0.15, "week4": 0.18, "drift": 0.03, "status": "increasing"},
        {"feature": "Card Age", "week1": -0.08, "week4": -0.11, "drift": -0.03, "status": "stable"},
    ])

    prediction_distribution = pd.DataFrame([
        {"score": "0-0.2", "count": 8420, "label": "Very Low"},
        {"score": "0.2-0.4", "count": 2840, "label": "Low"},
        {"score": "0.4-0.6", "count": 1230, "label": "Medium"},
        {"score": "0.6-0.8", "count": 680, "label": "High"},
        {"score": "0.8-1.0", "count": 430, "label": "Very High"},
    ])

    # --------------------------
    #  MODEL HEALTH STATUS
    # --------------------------
    st.subheader("📊 Model Health Overview")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("**Model Status**")
        st.metric(label="Status", value="Healthy")
        st.success("🟢 Active")

    with col2:
        st.markdown("**Current F1 Score**")
        st.metric("F1 Score", "0.925", "+0.015 from baseline")

    with col3:
        st.markdown("**Drift Status**")
        st.metric("Drift", "Low")
        st.info("Within threshold")

    with col4:
        st.markdown("**Last Retrained**")
        st.write("7 days ago")
        st.button("🔄 Retrain")

    st.divider()

    # --------------------------
    #  PERFORMANCE TREND CHART
    # --------------------------
    st.subheader("📈 Model Performance Trends")
    st.caption("Tracking model metrics over the past 4 weeks")

    trend_chart = (
        alt.Chart(performance_trend)
        .transform_fold(
            ["f1", "precision", "recall", "aucpr"],
            as_=["Metric", "Value"]
        )
        .mark_line(point=True)
        .encode(
            x=alt.X("week:N", title="Week"),
            y=alt.Y("Value:Q", title="Score", scale=alt.Scale(domain=[0.85, 1.0])),
            color=alt.Color("Metric:N", title="Metric"),
            tooltip=[
                alt.Tooltip("week:N", title="Week"),
                alt.Tooltip("Metric:N", title="Metric"),
                alt.Tooltip("Value:Q", title="Value", format=".3f"),
            ]
        )
        .properties(height=350)
    )

    st.altair_chart(trend_chart, use_container_width=True)

    st.divider()

    # --------------------------
    #  SHAP FEATURE DRIFT
    # --------------------------
    st.subheader("🧩 SHAP Feature Importance Drift")
    st.caption("Monitoring shifts in key feature importance scores")

    for _, row in shap_drift.iterrows():
        drift_color = "green" if row["status"] == "stable" else "orange"
        st.markdown(
            f"""
            **{row['feature']}**
            - Week 1: `{row['week1']:.2f}` → Week 4: `{row['week4']:.2f}`
            - Drift: :{drift_color}[{row['drift']:+.2f}]  
            - Status: :{drift_color}[{row['status'].capitalize()}]
            """
        )
        progress = abs(row["week4"]) / 0.45
        st.progress(min(progress, 1.0))

    st.divider()

    # --------------------------
    #  PREDICTION DISTRIBUTION
    # --------------------------
    st.subheader("🎯 Fraud Probability Distribution")
    st.caption("Distribution of model prediction confidence levels")

    dist_chart = (
        alt.Chart(prediction_distribution)
        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x="label:N",
            y="count:Q",
            tooltip=["label", "count"],
            color=alt.value("#3b82f6")
        )
        .properties(height=300)
    )
    st.altair_chart(dist_chart, use_container_width=True)

    st.divider()

    # --------------------------
    #  HEALTH & RECOMMENDATIONS
    # --------------------------
    st.subheader("⚙️ Alerts & Recommendations")
    col1, col2 = st.columns(2)

    with col1:
        st.success("**Model Health**")
        st.markdown(
            """
            ✅ Model performance is stable  
            ✅ Feature drift is minimal  
            ✅ Prediction distribution matches training data
            """
        )

    with col2:
        st.warning("**Recommendations**")
        st.markdown(
            """
            ⚠️ Monitor **NLP keyword importance** — slight upward trend  
            ⚠️ Retrain in **7–10 days** to maintain peak accuracy  
            ⚠️ Review **merchant category** patterns for new fraud vectors  
            """
        )