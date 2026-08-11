import streamlit as st
import requests
import os
from datetime import datetime
import pandas as pd
import psycopg2
import plotly.graph_objects as go

st.set_page_config(page_title="ScamShield Fraud Detection Dashboard", page_icon="🛡️", layout="wide")

# API endpoint URLs
API_BASE = os.getenv("API_URL", "http://localhost:8000")
API_URL = f"{API_BASE}/predict"
API_URL_EXPLAIN = f"{API_BASE}/predict/explain"

# Database Connection Helper
def query_db(query, params=None):
    db_url = os.getenv("DATABASE_URL", "postgresql://scamuser:scampass@localhost:5432/scamshield")
    conn = None
    try:
        conn = psycopg2.connect(db_url)
        df = pd.read_sql_query(query, conn, params=params)
        return df
    except Exception:
        # Fallback for docker-compose networking
        try:
            db_url_fallback = db_url.replace("localhost", "db")
            conn = psycopg2.connect(db_url_fallback)
            df = pd.read_sql_query(query, conn, params=params)
            return df
        except Exception as e2:
            st.warning(f"Could not connect to database for analytics: {e2}")
            return None
    finally:
        if conn:
            conn.close()

# Normal and Fraud templates for quick-fill
NORMAL_TEMPLATE = {
    "Time": 500.0,
    "Amount": 45.0,
    "V1": -0.5, "V2": 0.1, "V3": 1.2, "V4": -0.8, "V5": 0.4,
    "V6": -0.2, "V7": 0.3, "V8": 0.05, "V9": 0.15, "V10": -0.1,
    "V11": -0.6, "V12": 0.4, "V13": 0.9, "V14": 0.1, "V15": -0.3,
    "V16": 0.25, "V17": -0.05, "V18": 0.1, "V19": -0.2, "V20": -0.05,
    "V21": -0.1, "V22": 0.2, "V23": -0.1, "V24": 0.3, "V25": -0.2,
    "V26": 0.1, "V27": 0.02, "V28": 0.01
}

FRAUD_TEMPLATE = {
    "Time": 12000.0,
    "Amount": 850.0,
    "V1": -2.3, "V2": 1.8, "V3": -4.5, "V4": 5.2, "V5": -2.1,
    "V6": -1.5, "V7": -3.2, "V8": 0.9, "V9": -2.8, "V10": -5.6,
    "V11": 3.8, "V12": -7.2, "V13": 0.5, "V14": -8.9, "V15": -0.6,
    "V16": -5.3, "V17": -11.5, "V18": -4.2, "V19": 1.5, "V20": 0.8,
    "V21": 0.9, "V22": -0.5, "V23": -0.3, "V24": -0.1, "V25": 0.2,
    "V26": 0.4, "V27": 0.6, "V28": 0.2
}

# Sidebar Controls
st.sidebar.title("🛡️ ScamShield Controls")
st.sidebar.write("Load realistic sample data to test the system:")

if st.sidebar.button("Load Normal Transaction"):
    for k, v in NORMAL_TEMPLATE.items():
        st.session_state[k] = v

if st.sidebar.button("Load Fraud Transaction"):
    for k, v in FRAUD_TEMPLATE.items():
        st.session_state[k] = v

# Initialize session state with default values
default_values = {
    "Time": 10000.0,
    "Amount": 100.0,
    **{f"V{i}": 0.0 for i in range(1, 29)}
}
for k, v in default_values.items():
    if k not in st.session_state:
        st.session_state[k] = v

st.title("🛡️ ScamShield Fraud Intelligence Center")
st.write("Real-time transaction profiling, explainable AI diagnostics, and database analytics.")

# Render tab structure
tab1, tab2, tab3 = st.tabs(["🔍 Single Prediction", "📊 Explainability (SHAP)", "📈 Real-time Analytics"])

def render_parameters_form(prefix):
    st.subheader("Transaction Parameters")
    col_time, col_amount = st.columns(2)
    with col_time:
        time_val = st.number_input("Time (seconds elapsed)", key=f"{prefix}_Time", value=st.session_state["Time"], step=1.0)
    with col_amount:
        amount_val = st.number_input("Amount ($)", key=f"{prefix}_Amount", value=st.session_state["Amount"], step=1.0)

    st.subheader("Anonymized PCA Features (V1 - V28)")
    v_values = {}
    v_cols = st.columns(4)
    for i in range(1, 29):
        col_idx = (i - 1) % 4
        key = f"V{i}"
        with v_cols[col_idx]:
            v_values[key] = st.number_input(key, key=f"{prefix}_{key}", value=st.session_state[key], step=0.1)
            
    # Sync helper to write back to session state
    st.session_state["Time"] = time_val
    st.session_state["Amount"] = amount_val
    for i in range(1, 29):
        st.session_state[f"V{i}"] = v_values[f"V{i}"]

    return {
        "Time": time_val,
        "Amount": amount_val,
        **{f"V{i}": v_values[f"V{i}"] for i in range(1, 29)}
    }

# ==================== TAB 1: SINGLE PREDICTION ====================
with tab1:
    payload = render_parameters_form("predict")
    st.write("---")
    if st.button("Predict Fraud Risk", type="primary", key="btn_predict"):
        try:
            response = requests.post(API_URL, json=payload, timeout=5)
            if response.status_code == 200:
                result = response.json()
                prob = result["fraud_probability"]
                risk = result["risk_level"]
                pred = result["prediction"]
                timestamp_str = result["timestamp"]

                st.write("### 🔍 Risk Analysis Result")
                res_col1, res_col2, res_col3 = st.columns(3)
                res_col1.metric("Fraud Probability", f"{prob:.4f}")
                res_col2.metric("Risk Level", risk)
                res_col3.metric("Prediction Class", "Fraud (1)" if pred == 1 else "Normal (0)")

                if risk == "HIGH":
                    st.error(f"🚨 **HIGH RISK**: Flagged at {timestamp_str}")
                elif risk == "MEDIUM":
                    st.warning(f"⚠️ **MEDIUM RISK**: Review recommended. Timestamp: {timestamp_str}")
                else:
                    st.success(f"✅ **LOW RISK**: Transaction clean. Timestamp: {timestamp_str}")
            else:
                st.error(f"API Error (Status Code {response.status_code}): {response.text}")
        except Exception as e:
            st.error(f"Connection failed: {e}")

# ==================== TAB 2: EXPLAINABILITY ====================
with tab2:
    payload = render_parameters_form("explain")
    st.write("---")
    if st.button("Explain Fraud Risk", type="primary", key="btn_explain"):
        try:
            response = requests.post(API_URL_EXPLAIN, json=payload, timeout=5)
            if response.status_code == 200:
                result = response.json()
                prob = result["fraud_probability"]
                risk = result["risk_level"]
                pred = result["prediction"]
                timestamp_str = result["timestamp"]
                top_factors = result["top_risk_factors"]
                baseline = result["baseline_probability"]

                st.write("### 🔍 Explainable Risk Diagnostics")
                
                # Gauge representation using metric
                delta_val = prob - baseline
                st.metric(
                    label="Transaction Fraud Risk Score",
                    value=f"{prob:.2%}",
                    delta=f"{delta_val:+.2%} vs Baseline Expectation ({baseline:.2%})",
                    delta_color="inverse"
                )

                # Horizontal Bar Chart using Plotly
                if top_factors:
                    reversed_factors = list(reversed(top_factors))
                    y_features = [f["feature_name"] for f in reversed_factors]
                    x_shaps = [f["shap_value"] for f in reversed_factors]
                    colors = ["#ff4b4b" if val > 0 else "#2eb872" for val in x_shaps]

                    fig = go.Figure()
                    fig.add_trace(go.Bar(
                        x=x_shaps,
                        y=y_features,
                        orientation='h',
                        marker_color=colors,
                        text=[f"{val:+.4f}" for val in x_shaps],
                        textposition='auto'
                    ))
                    fig.update_layout(
                        title="Top 5 Features Driving Risk Shift (SHAP Values)",
                        xaxis_title="SHAP Value Contribution",
                        yaxis_title="Feature Name",
                        margin=dict(l=100, r=20, t=40, b=40),
                        height=350,
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)'
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    # Plain-English Explanation
                    pos_drivers = [f for f in top_factors if f["shap_value"] > 0]
                    neg_drivers = [f for f in top_factors if f["shap_value"] < 0]

                    exp_sentences = []
                    if pos_drivers:
                        top_pos = pos_drivers[0]
                        exp_sentences.append(f"**{top_pos['feature_name']}** was unusually high/low ({top_pos['feature_value']:.2f}), shifting risk up by {top_pos['shap_value']:.2%}")
                    if neg_drivers:
                        top_neg = neg_drivers[0]
                        exp_sentences.append(f"**{top_neg['feature_name']}** was {top_neg['feature_value']:.2f}, dampening risk by {top_neg['shap_value']:.2%}")

                    explanation_str = f"This transaction was flagged as **{risk}** risk primarily because "
                    explanation_str += " and ".join(exp_sentences) + "."
                    st.info(explanation_str)
                else:
                    st.warning("SHAP explanation data could not be computed by the server.")
            else:
                st.error(f"API Error (Status Code {response.status_code}): {response.text}")
        except Exception as e:
            st.error(f"Connection failed: {e}")

# ==================== TAB 3: REAL-TIME ANALYTICS ====================
with tab3:
    st.subheader("PostgreSQL Real-Time Analytics Dashboard")
    
    # Run database queries
    df_metrics = query_db(
        """
        SELECT 
            COUNT(*) AS total_today,
            COALESCE(AVG(prediction), 0.0) AS fraud_rate_today,
            COALESCE(AVG(response_time_ms), 0.0) AS avg_res_time,
            SUM(CASE WHEN risk_level = 'HIGH' THEN 1 ELSE 0 END) AS high_risk_today
        FROM predictions
        WHERE timestamp >= CURRENT_DATE;
        """
    )
    
    df_hourly = query_db(
        """
        SELECT 
            DATE_TRUNC('hour', timestamp) AS hour,
            AVG(fraud_probability) AS fraud_rate
        FROM predictions
        WHERE timestamp >= NOW() - INTERVAL '24 hours'
        GROUP BY hour
        ORDER BY hour;
        """
    )
    
    df_distribution = query_db(
        """
        SELECT risk_level, COUNT(*) AS count
        FROM predictions
        GROUP BY risk_level;
        """
    )

    # Check database presence
    if df_metrics is None or df_metrics.empty or df_metrics.iloc[0]["total_today"] == 0:
        st.info("📊 Connect to PostgreSQL database to view analytics. Submit a few predictions first to populate data.")
    else:
        # 4 top metrics columns
        tot = df_metrics.iloc[0]["total_today"]
        fr = df_metrics.iloc[0]["fraud_rate_today"]
        rt = df_metrics.iloc[0]["avg_res_time"]
        hr = df_metrics.iloc[0]["high_risk_today"]

        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        m_col1.metric("Total Predictions Today", f"{tot}")
        m_col2.metric("Fraud Rate Today", f"{fr:.2%}")
        m_col3.metric("Avg Response Time", f"{rt:.1f} ms")
        m_col4.metric("High Risk Count Today", f"{hr}")

        st.write("---")
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            st.write("#### Hourly Fraud Probability (Last 24 Hours)")
            if df_hourly is not None and not df_hourly.empty:
                df_hourly_sorted = df_hourly.set_index("hour")
                st.line_chart(df_hourly_sorted["fraud_rate"])
            else:
                st.write("No hourly data available yet.")

        with chart_col2:
            st.write("#### Risk Level Distribution")
            if df_distribution is not None and not df_distribution.empty:
                df_dist_sorted = df_distribution.set_index("risk_level")
                st.bar_chart(df_dist_sorted["count"])
            else:
                st.write("No risk distribution data available.")
