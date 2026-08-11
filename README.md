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

🚀 Getting Started
1. Prerequisites
Ensure Python 3.10+ and Git are installed on your machine.

2. Clone the Repository
Bash


git clone [https://github.com/YOUR_USERNAME/scamshield-fraud-detection-ml.git](https://github.com/YOUR_USERNAME/scamshield-fraud-detection-ml.git)
cd scamshield-fraud-detection-ml
3. Create & Activate Virtual Environment
Linux / macOS:

Bash


python3 -m venv .venv
source .venv/bin/activate
Windows (Command Prompt / PowerShell):

DOS


python -m venv .venv
.venv\Scripts\activate
4. Install Dependencies
Bash


python -m pip install --upgrade pip
pip install -r requirements.txt
⚙️ Running the Application
Option A: Running Local Services
Start the FastAPI Backend API:

Bash


source .venv/bin/activate
uvicorn api.main:app --reload --port 8000
API Root: http://127.0.0.1:8000

Interactive Swagger UI: http://127.0.0.1:8000/docs

Start the Streamlit Dashboard (In a new terminal tab):

Bash


source .venv/bin/activate
streamlit run dashboard/app.py
Dashboard URL: http://localhost:8501

Option B: Running with Docker Compose
To spin up the entire application stack in containerized mode:

Bash


docker-compose up --build
🔐 API Authorization & Example Request
To authorize API requests in Swagger UI (http://127.0.0.1:8000/docs):

Click Authorize on the top right.

Enter the secret key: scamshield_secret_key_2026.

Submit a payload to POST /predict:

JSON


{
  "amount": 180000.00,
  "oldbalanceOrg": 180000.00,
  "newbalanceOrig": 0.00,
  "oldbalanceDest": 0.00,
  "newbalanceDest": 180000.00,
  "transaction_type": "TRANSFER"
}
📜 License & Acknowledgments
This project uses open-source components and datasets licensed under the MIT License.
