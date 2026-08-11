import os
import json
import logging
import pandas as pd
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from imblearn.over_sampling import SMOTE
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
import joblib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("retrain")

def retrain_model():
    data_path = "data/creditcard.csv"
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Dataset not found at {data_path}")

    logger.info("Loading dataset...")
    df = pd.read_csv(data_path)
    X = df.drop("Class", axis=1)
    y = df["Class"]

    logger.info("Splitting data into train/test...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )

    logger.info("Fitting and applying StandardScaler on ['Time', 'Amount']...")
    scaler = StandardScaler()
    # Correct scaling sequence: ['Time', 'Amount']
    X_train[['Time', 'Amount']] = scaler.fit_transform(X_train[['Time', 'Amount']])
    X_test[['Time', 'Amount']] = scaler.transform(X_test[['Time', 'Amount']])

    logger.info("Applying SMOTE resampling...")
    smote = SMOTE(random_state=42)
    X_train_resampled, y_train_resampled = smote.fit_resample(X_train, y_train)

    logger.info("Training Random Forest Classifier...")
    # Exact original hyperparameters
    model = RandomForestClassifier(
        n_estimators=50,
        max_depth=10,
        n_jobs=-1,
        random_state=42
    )
    model.fit(X_train_resampled, y_train_resampled)

    logger.info("Evaluating retrained model...")
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)[:, 1]

    metrics = {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision": float(precision_score(y_test, y_pred)),
        "recall": float(recall_score(y_test, y_pred)),
        "f1": float(f1_score(y_test, y_pred)),
        "roc_auc": float(roc_auc_score(y_test, y_pred_proba)),
        "timestamp": datetime.now().isoformat()
    }

    logger.info(f"Retrained Model Metrics:\n{json.dumps(metrics, indent=2)}")

    # Define paths
    os.makedirs("models", exist_ok=True)
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M")
    model_version_path = f"models/fraud_model_v{timestamp_str}.pkl"
    scaler_version_path = f"models/scaler_v{timestamp_str}.pkl"

    # Save versioned artifacts
    logger.info(f"Saving versioned model to {model_version_path}...")
    joblib.dump(model, model_version_path)
    joblib.dump(scaler, scaler_version_path)

    # Overwrite main model and scaler artifacts (symlink replacement logic)
    logger.info("Updating production artifacts models/fraud_model.pkl and models/scaler.pkl...")
    joblib.dump(model, "models/fraud_model.pkl")
    joblib.dump(scaler, "models/scaler.pkl")

    # Save metrics to models/metrics_{timestamp}.json
    metrics_path = f"models/metrics_{timestamp_str}.json"
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Saved training metrics to {metrics_path}")

    return metrics

if __name__ == "__main__":
    retrain_model()
