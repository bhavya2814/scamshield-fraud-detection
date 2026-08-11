import time
import requests
import sys

base_url = "http://localhost:8088"
login_url = f"{base_url}/api/v1/security/login"

print("Waiting for Apache Superset to start...")
max_retries = 30
session = requests.Session()
token = None

for i in range(max_retries):
    try:
        r = session.post(login_url, json={
            "username": "admin",
            "password": "admin",
            "provider": "db"
        }, timeout=5)
        if r.status_code == 200:
            token_data = r.json()
            token = token_data.get("access_token") or token_data.get("result", {}).get("access_token")
            print("Successfully authenticated with Superset!")
            break
    except Exception:
        pass
    print(f"Waiting for Superset... (attempt {i+1}/{max_retries})")
    time.sleep(5)

if not token:
    print("Error: Could not connect to Superset API.")
    sys.exit(1)

# Set authorization header
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# 1. Create database connection to PostgreSQL scamshield db
# In docker-compose, Superset uses the hostname 'db' to connect to Postgres.
db_payload = {
    "database_name": "scamshield_postgres",
    "sqlalchemy_uri": "postgresql://scamuser:scampass@db:5432/scamshield"
}

db_url = f"{base_url}/api/v1/database/"
r = session.post(db_url, json=db_payload, headers=headers)
if r.status_code not in [200, 201]:
    # It might already exist, let's fetch list of databases
    r_list = session.get(db_url, headers=headers)
    db_id = None
    for db in r_list.json().get("result", []):
        if db["database_name"] == "scamshield_postgres":
            db_id = db["id"]
            break
    if not db_id:
        print("Failed to create/find database connection in Superset:", r.text)
        sys.exit(1)
else:
    db_data = r.json()
    db_id = db_data.get("id") or db_data.get("result", {}).get("id")

print(f"Using database ID: {db_id}")

# 2. Create the 4 datasets (virtual table datasets based on SQL queries)
queries = {
    "hourly_fraud": {
        "table_name": "Hourly Fraud Rate (Last 7 Days)",
        "sql": "SELECT DATE_TRUNC('hour', timestamp) AS hour_ts, AVG(fraud_probability) AS avg_fraud_prob FROM predictions GROUP BY 1 ORDER BY 1"
    },
    "risk_dist": {
        "table_name": "Risk Level Distribution",
        "sql": "SELECT risk_level, COUNT(*) AS cnt FROM predictions GROUP BY 1"
    },
    "fraud_today": {
        "table_name": "Total Fraud Detected Today",
        "sql": "SELECT COUNT(*) AS total_fraud FROM predictions WHERE prediction = 1 AND timestamp >= CURRENT_DATE"
    },
    "amount_vs_fraud": {
        "table_name": "Amount Bucket vs Avg Fraud Probability",
        "sql": """
        SELECT 
            CASE 
                WHEN amount < 10 THEN '1_micro'
                WHEN amount >= 10 AND amount < 100 THEN '2_small'
                WHEN amount >= 100 AND amount < 1000 THEN '3_medium'
                ELSE '4_large'
            END AS amount_bucket,
            AVG(fraud_probability) AS avg_fraud_probability
        FROM predictions
        GROUP BY amount_bucket
        ORDER BY amount_bucket
        """
    }
}

dataset_ids = {}
dataset_url = f"{base_url}/api/v1/dataset/"

for key, q in queries.items():
    dataset_payload = {
        "database": db_id,
        "table_name": q["table_name"],
        "schema": "public",
        "sql": q["sql"]
    }
    r = session.post(dataset_url, json=dataset_payload, headers=headers)
    if r.status_code not in [200, 201]:
        # It might already exist, let's fetch list
        r_list = session.get(dataset_url, headers=headers)
        ds_id = None
        for ds in r_list.json().get("result", []):
            if ds["table_name"] == q["table_name"]:
                ds_id = ds["id"]
                break
        if not ds_id:
            print(f"Failed to create/find dataset {q['table_name']}:", r.text)
            sys.exit(1)
        dataset_ids[key] = ds_id
    else:
        ds_data = r.json()
        dataset_ids[key] = ds_data.get("id") or ds_data.get("result", {}).get("id")

print("Created Datasets:", dataset_ids)

# 3. Create the 4 charts
charts_configs = [
    {
        "slice_name": "Hourly Fraud Rate (Last 7 Days)",
        "viz_type": "line",
        "datasource_id": dataset_ids["hourly_fraud"],
        "datasource_type": "table",
        "params": '{"metrics": ["avg_fraud_prob"], "groupby": ["hour_ts"], "viz_type": "line"}'
    },
    {
        "slice_name": "Risk Level Distribution",
        "viz_type": "pie",
        "datasource_id": dataset_ids["risk_dist"],
        "datasource_type": "table",
        "params": '{"metric": "cnt", "groupby": ["risk_level"], "viz_type": "pie"}'
    },
    {
        "slice_name": "Total Fraud Detected Today",
        "viz_type": "big_number_total",
        "datasource_id": dataset_ids["fraud_today"],
        "datasource_type": "table",
        "params": '{"metric": "total_fraud", "viz_type": "big_number_total"}'
    },
    {
        "slice_name": "Amount Bucket vs Avg Fraud Probability",
        "viz_type": "dist_bar",
        "datasource_id": dataset_ids["amount_vs_fraud"],
        "datasource_type": "table",
        "params": '{"metrics": ["avg_fraud_probability"], "groupby": ["amount_bucket"], "viz_type": "dist_bar"}'
    }
]

chart_ids = []
chart_url = f"{base_url}/api/v1/chart/"

for chart in charts_configs:
    r = session.post(chart_url, json=chart, headers=headers)
    if r.status_code not in [200, 201]:
        # It might already exist, let's fetch list
        r_list = session.get(chart_url, headers=headers)
        c_id = None
        for c in r_list.json().get("result", []):
            if c["slice_name"] == chart["slice_name"]:
                c_id = c["id"]
                break
        if not c_id:
            print(f"Failed to create/find chart {chart['slice_name']}:", r.text)
            sys.exit(1)
        chart_ids.append(c_id)
    else:
        c_data = r.json()
        chart_ids.append(c_data.get("id") or c_data.get("result", {}).get("id"))

print("Created Charts:", chart_ids)

# 4. Create the Dashboard "ScamShield Fraud Intelligence" containing all 4 charts
dashboard_url = f"{base_url}/api/v1/dashboard/"
dashboard_payload = {
    "dashboard_title": "ScamShield Fraud Intelligence",
    "slices": chart_ids,
    "published": True
}

r = session.post(dashboard_url, json=dashboard_payload, headers=headers)
if r.status_code not in [200, 201]:
    # It might already exist, fetch list
    r_list = session.get(dashboard_url, headers=headers)
    dashboard_id = None
    for dbd in r_list.json().get("result", []):
        if dbd["dashboard_title"] == "ScamShield Fraud Intelligence":
            dashboard_id = dbd["id"]
            break
    if not dashboard_id:
        print("Failed to create/find dashboard:", r.text)
        sys.exit(1)
else:
    dbd_data = r.json()
    dashboard_id = dbd_data.get("id") or dbd_data.get("result", {}).get("id")

print(f"\n🚀 Setup Complete!")
print(f"Dashboard 'ScamShield Fraud Intelligence' is ready.")
print(f"Dashboard URL: http://localhost:8088/superset/dashboard/{dashboard_id}/")
