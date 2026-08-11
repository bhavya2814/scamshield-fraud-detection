# 🛡️ ScamShield — ML-Powered Fraud Detection System

**ScamShield** is a real-time machine learning system designed to detect and flag fraudulent financial transactions. The system serves pre-trained ML models via a **FastAPI REST API**, exposes model explainability via **SHAP**, presents risk analytics through an interactive **Streamlit dashboard**, and supports structured **SQL transaction logging**.

---

## 🏗️ System Architecture

┌────────────────────────┐
                              │   Streamlit Dashboard  │
                              │   (Port: 8501)         │
                              └───────────┬────────────┘
                                          │ HTTP Requests
                                          ▼
┌───────────────────────┐         ┌────────────────────────┐         ┌────────────────────────┐
│  Client / API Consumer│ ──────> │  FastAPI REST Service  │ ──────> │   Scikit-Learn / SHAP  │
│  (X-API-KEY Protected)│ <────── │  (Port: 8000)          │ <────── │   Inference Engine     │
└───────────────────────┘         └───────────┬────────────┘         └────────────────────────┘
│ Logging
▼
┌────────────────────────┐
│   SQL Database         │
│   (SQLite / Postgres)  │
└────────────────────────┘


---

## ✨ Key Features

* **Real-Time API Predictions:** Fast inference using FastAPI with Pydantic request/response validation.
* **API Key Security:** Custom header authentication (`X-API-KEY`) to protect endpoints against unauthorized calls.
* **Model Explainability (SHAP):** Features a `/predict/explain` endpoint using **SHAP TreeExplainer** to highlight exact feature contributions for every flagged prediction.
* **Interactive Dashboard:** Streamlit UI to visualize fraud probability scores, metrics, and transaction flags.
* **Modular Codebase:** Structured directory layout separating model loading, web routing, dashboards, and database persistence.

---

## 🛠️ Tech Stack & Dependencies

* **Language:** Python 3.11+
* **Frameworks & APIs:** FastAPI, Uvicorn, Streamlit
* **Machine Learning & Analytics:** Scikit-learn, XGBoost, SHAP, Pandas, NumPy
* **Data Processing & Storage:** SQL (SQLite/PostgreSQL), Pydantic
* **DevOps & Containers:** Docker, Docker Compose

---

## 📂 Repository Structure

```text
scamshield-fraud-detection-ml/

├── api/                   # FastAPI backend application & routers
│   └── main.py            # Main API entrypoint and routes
├── dashboard/             # Streamlit dashboard scripts
│   └── app.py             # Frontend dashboard entrypoint
├── models/                # Pre-trained ML classifiers & scalers (.pkl)
├── notebooks/             # Exploratory Data Analysis & Model Training
├── sql/                   # Database schemas & SQL setup scripts
├── .venv/                 # Python Virtual Environment (git-ignored)
├── Dockerfile             # Container configuration
├── docker-compose.yml     # Multi-container service orchestrator
├── requirements.txt       # Project dependencies
└── README.md              # Project documentation
