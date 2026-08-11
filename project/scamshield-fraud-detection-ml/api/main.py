from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel, Field
import joblib
import numpy as np
from datetime import datetime
import asyncpg
import os
import time
import shap

app = FastAPI(title="ScamShield Fraud Detection API")

# Initialize startup time and in-memory counters
START_TIME = datetime.utcnow()
total_predictions = 0
fraud_count = 0
total_response_time_ms = 0.0

# Load model and scaler
model = joblib.load("models/fraud_model.pkl")
scaler = joblib.load("models/scaler.pkl")

# Cached SHAP Explainer
explainer = None

# Database and Model Version Configuration
DATABASE_URL = os.getenv("DATABASE_URL")
MODEL_VERSION = os.getenv("MODEL_VERSION", "random_forest_v1.0")

@app.on_event("startup")
async def startup_event():
    global explainer
    # Initialize the SHAP TreeExplainer
    try:
        explainer = shap.TreeExplainer(model)
        print("SHAP TreeExplainer cached successfully.")
    except Exception as e:
        print(f"Error caching SHAP explainer: {e}")
        explainer = None

    if DATABASE_URL:
        try:
            app.state.pool = await asyncpg.create_pool(DATABASE_URL)
            print("PostgreSQL connection pool created successfully.")
        except Exception as e:
            print(f"Error creating PostgreSQL connection pool: {e}")
            app.state.pool = None
    else:
        print("DATABASE_URL env var not set. Database logging is disabled.")
        app.state.pool = None

@app.on_event("shutdown")
async def shutdown_event():
    if getattr(app.state, "pool", None):
        await app.state.pool.close()
        print("PostgreSQL connection pool closed.")

class TransactionInput(BaseModel):
    Time: float = Field(..., example=10000.0)
    V1: float = Field(0.0)
    V2: float = Field(0.0)
    V3: float = Field(0.0)
    V4: float = Field(0.0)
    V5: float = Field(0.0)
    V6: float = Field(0.0)
    V7: float = Field(0.0)
    V8: float = Field(0.0)
    V9: float = Field(0.0)
    V10: float = Field(0.0)
    V11: float = Field(0.0)
    V12: float = Field(0.0)
    V13: float = Field(0.0)
    V14: float = Field(0.0)
    V15: float = Field(0.0)
    V16: float = Field(0.0)
    V17: float = Field(0.0)
    V18: float = Field(0.0)
    V19: float = Field(0.0)
    V20: float = Field(0.0)
    V21: float = Field(0.0)
    V22: float = Field(0.0)
    V23: float = Field(0.0)
    V24: float = Field(0.0)
    V25: float = Field(0.0)
    V26: float = Field(0.0)
    V27: float = Field(0.0)
    V28: float = Field(0.0)
    Amount: float = Field(..., example=100.0)

async def log_to_db(amount: float, fraud_probability: float, risk_level: str, prediction: int, response_time_ms: int, v1: float, v2: float, v3: float, v4: float, v5: float, explained: bool = False):
    pool = getattr(app.state, "pool", None)
    if pool:
        try:
            async with pool.acquire() as connection:
                await connection.execute(
                    """
                    INSERT INTO predictions (amount, fraud_probability, risk_level, prediction, response_time_ms, v1, v2, v3, v4, v5, explained)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                    """,
                    amount, fraud_probability, risk_level, prediction, response_time_ms, v1, v2, v3, v4, v5, explained
                )
        except Exception as e:
            print(f"Error logging transaction to database: {e}")

@app.get("/")
def home():
    return {"message": "ScamShield API running"}

@app.get("/health")
async def health():
    db_connected = False
    pool = getattr(app.state, "pool", None)
    if pool:
        try:
            async with pool.acquire() as connection:
                await connection.fetchval("SELECT 1")
                db_connected = True
        except Exception as e:
            print(f"Health check DB ping failed: {e}")
            db_connected = False

    uptime_seconds = (datetime.utcnow() - START_TIME).total_seconds()
    return {
        "status": "healthy",
        "model_version": MODEL_VERSION,
        "uptime_seconds": uptime_seconds,
        "db_connected": db_connected
    }

@app.get("/metrics")
def metrics():
    rate = 0.0
    avg_res_time = 0.0
    if total_predictions > 0:
        rate = fraud_count / total_predictions
        avg_res_time = total_response_time_ms / total_predictions

    return {
        "total_predictions": total_predictions,
        "fraud_detected": fraud_count,
        "fraud_rate": rate,
        "avg_response_time_ms": avg_res_time,
        "model_version": MODEL_VERSION
    }

@app.post("/predict")
async def predict(tx: TransactionInput, background_tasks: BackgroundTasks):
    global total_predictions, fraud_count, total_response_time_ms
    start_time = time.time()

    # Build feature vector by name to prevent ordering issues
    feature_keys = ["Time"] + [f"V{i}" for i in range(1, 29)] + ["Amount"]
    tx_dict = tx.dict()
    feature_vector = np.array([tx_dict[k] for k in feature_keys]).reshape(1, -1)

    # Scale Time (index 0) and Amount (index -1)
    feature_vector[:, [0, -1]] = scaler.transform(feature_vector[:, [0, -1]])

    # Get prediction probability
    prob = model.predict_proba(feature_vector)[0][1]

    # Align code thresholds to README: LOW < 0.3, MEDIUM 0.3-0.7, HIGH > 0.7
    if prob > 0.7:
        risk = "HIGH"
    elif prob >= 0.3:
        risk = "MEDIUM"
    else:
        risk = "LOW"

    prediction = int(prob >= 0.5)
    timestamp = datetime.utcnow().isoformat()
    
    # Calculate response time in ms
    response_time_ms = int((time.time() - start_time) * 1000)

    # Update in-memory metrics
    total_predictions += 1
    if prediction == 1:
        fraud_count += 1
    total_response_time_ms += response_time_ms

    # Log to PostgreSQL in the background
    background_tasks.add_task(
        log_to_db,
        tx.Amount,
        float(prob),
        risk,
        prediction,
        response_time_ms,
        tx.V1,
        tx.V2,
        tx.V3,
        tx.V4,
        tx.V5,
        False
    )

    return {
        "fraud_probability": float(prob),
        "risk_level": risk,
        "prediction": prediction,
        "timestamp": timestamp
    }

@app.post("/predict/explain")
async def predict_explain(tx: TransactionInput, background_tasks: BackgroundTasks):
    global total_predictions, fraud_count, total_response_time_ms, explainer
    start_time = time.time()

    # Build feature vector by name to prevent ordering issues
    feature_keys = ["Time"] + [f"V{i}" for i in range(1, 29)] + ["Amount"]
    tx_dict = tx.dict()
    feature_values = [tx_dict[k] for k in feature_keys]
    feature_vector = np.array(feature_values).reshape(1, -1)

    # Scale Time (index 0) and Amount (index -1)
    feature_vector[:, [0, -1]] = scaler.transform(feature_vector[:, [0, -1]])

    # Get prediction probability
    prob = model.predict_proba(feature_vector)[0][1]

    # Align code thresholds to README: LOW < 0.3, MEDIUM 0.3-0.7, HIGH > 0.7
    if prob > 0.7:
        risk = "HIGH"
    elif prob >= 0.3:
        risk = "MEDIUM"
    else:
        risk = "LOW"

    prediction = int(prob >= 0.5)
    timestamp = datetime.utcnow().isoformat()
    
    # Calculate response time in ms
    response_time_ms = int((time.time() - start_time) * 1000)

    # Update in-memory metrics
    total_predictions += 1
    if prediction == 1:
        fraud_count += 1
    total_response_time_ms += response_time_ms

    # Calculate SHAP explanation (class 1)
    top_risk_factors = []
    baseline_probability = 0.5
    if explainer is not None:
        try:
            shap_vals = explainer.shap_values(feature_vector)
            # TreeExplainer returns shape (1, 30, 2)
            class_1_shap = shap_vals[0, :, 1]
            
            factors = []
            for name, val, sv in zip(feature_keys, feature_values, class_1_shap):
                direction = "increases_risk" if sv > 0 else "decreases_risk"
                factors.append({
                    "feature_name": name,
                    "shap_value": float(sv),
                    "direction": direction,
                    "feature_value": float(val)
                })
            
            # Sort by absolute SHAP value descending, take top 5
            top_risk_factors = sorted(factors, key=lambda x: abs(x["shap_value"]), reverse=True)[:5]
            
            # Extract baseline probability
            if isinstance(explainer.expected_value, (list, np.ndarray)) and len(explainer.expected_value) > 1:
                baseline_probability = float(explainer.expected_value[1])
            else:
                baseline_probability = float(explainer.expected_value)
        except Exception as e:
            print(f"Error generating SHAP explanation: {e}")

    # Log to PostgreSQL with explained=True
    background_tasks.add_task(
        log_to_db,
        tx.Amount,
        float(prob),
        risk,
        prediction,
        response_time_ms,
        tx.V1,
        tx.V2,
        tx.V3,
        tx.V4,
        tx.V5,
        True
    )

    return {
        "fraud_probability": float(prob),
        "risk_level": risk,
        "prediction": prediction,
        "timestamp": timestamp,
        "top_risk_factors": top_risk_factors,
        "baseline_probability": baseline_probability
    }
