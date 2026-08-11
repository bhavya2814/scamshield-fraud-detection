import os

# Overwrite environment variable so uvicorn does not attempt real DB connections
os.environ["DATABASE_URL"] = ""

import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "model_version" in data
    assert "uptime_seconds" in data
    assert "db_connected" in data
    assert data["status"] == "healthy"
    assert data["db_connected"] is False

def test_metrics():
    response = client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "total_predictions" in data
    assert "fraud_detected" in data
    assert "fraud_rate" in data
    assert "avg_response_time_ms" in data
    assert "model_version" in data

def test_predict_valid():
    # V1=-1.36, V2=-0.07, rest zeros, Amount=149.62
    payload = {
        "Time": 0.0,
        "Amount": 149.62,
        "V1": -1.36,
        "V2": -0.07,
        **{f"V{i}": 0.0 for i in range(3, 29)}
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "fraud_probability" in data
    assert "risk_level" in data
    assert "prediction" in data
    assert "timestamp" in data
    assert 0.0 <= data["fraud_probability"] <= 1.0

def test_predict_missing():
    # missing Time and Amount
    payload = {
        **{f"V{i}": 0.0 for i in range(1, 29)}
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 422
