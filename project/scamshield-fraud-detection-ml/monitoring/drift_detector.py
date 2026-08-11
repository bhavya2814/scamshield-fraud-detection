import os
import time
import logging
import pandas as pd
import psycopg2
from datetime import datetime
from evidently.report import Report
from evidently.metric_preset import DataDriftPreset, DataQualityPreset

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("drift_detector")

# Configure folders
REPORTS_DIR = "monitoring/reports"
os.makedirs(REPORTS_DIR, exist_ok=True)

def generate_drift_report(current_data: pd.DataFrame) -> dict:
    # Load reference data
    ref_path = "data/creditcard.csv"
    if not os.path.exists(ref_path):
        raise FileNotFoundError(f"Reference data not found at {ref_path}")
        
    ref_df = pd.read_csv(ref_path, nrows=10000)
    
    # We only drift analyze the columns present in the predictions DB: V1-V5 and Amount
    cols_to_compare = ["V1", "V2", "V3", "V4", "V5", "Amount"]
    
    # Ensure current_data columns match uppercase names
    current_data = current_data.rename(columns={
        "amount": "Amount",
        "v1": "V1",
        "v2": "V2",
        "v3": "V3",
        "v4": "V4",
        "v5": "V5"
    })
    
    ref_compare = ref_df[cols_to_compare]
    cur_compare = current_data[cols_to_compare]
    
    # Run Evidently report
    report = Report(metrics=[
        DataDriftPreset(),
        DataQualityPreset()
    ])
    report.run(reference_data=ref_compare, current_data=cur_compare)
    
    # Save HTML report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = os.path.join(REPORTS_DIR, f"drift_report_{timestamp}.html")
    report.save_html(report_path)
    logger.info(f"Drift report saved to {report_path}")
    
    # Parse results from report dict
    report_dict = report.as_dict()
    metrics = report_dict.get("metrics", [])
    
    drift_detected = False
    drift_score = 0.0
    drifted_features = []
    
    # Find dataset drift metric
    for metric_val in metrics:
        metric_class = metric_val.get("metric")
        if metric_class == "DatasetDriftMetric":
            result = metric_val.get("result", {})
            drift_detected = result.get("dataset_drift", False)
            drift_score = result.get("drift_share", 0.0)
        elif metric_class == "DataDriftTable":
            result = metric_val.get("result", {})
            drift_by_columns = result.get("drift_by_columns", {})
            for col, col_info in drift_by_columns.items():
                if col_info.get("drift_detected", False):
                    drifted_features.append(col)
                    
    return {
        "drift_detected": bool(drift_detected),
        "drifted_features": drifted_features,
        "drift_score": float(drift_score)
    }

def check_and_retrain(drift_score: float, threshold: float = 0.15) -> bool:
    if drift_score > threshold:
        logger.warning(f"🚨 ALERT: Data drift detected! Drift score {drift_score:.4f} exceeds threshold {threshold:.4f}.")
        return True
    return False

if __name__ == "__main__":
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        logger.error("DATABASE_URL environment variable is not set.")
        exit(1)
        
    logger.info("Connecting to PostgreSQL database to pull predictions...")
    try:
        conn = psycopg2.connect(DATABASE_URL)
        query = "SELECT amount, v1, v2, v3, v4, v5 FROM predictions ORDER BY timestamp DESC LIMIT 1000;"
        current_df = pd.read_sql_query(query, conn)
        conn.close()
    except Exception as e:
        logger.error(f"Failed to fetch predictions from database: {e}")
        exit(1)
        
    if current_df.empty:
        logger.error("No predictions found in the database to analyze.")
        exit(1)
        
    logger.info(f"Fetched {len(current_df)} prediction records. Running drift analysis...")
    try:
        report_res = generate_drift_report(current_df)
        logger.info(f"Drift Analysis Summary: {report_res}")
        
        need_retrain = check_and_retrain(report_res["drift_score"])
        if need_retrain:
            logger.info("Triggering model retraining...")
            # We can import retrain here if needed
    except Exception as e:
        logger.error(f"Error running drift detection: {e}")
