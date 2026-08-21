"""
sensor_network_thunderstorm_ml.py

Trains a RandomForest model on thunderstorm_raw_data.csv
and saves it as storm_model.pkl for the web dashboard.

This script includes the custom weather labeling rule internally, 
eliminating the need for a separate label update script.
"""

import os
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
import joblib

# Path Resolution
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "thunderstorm_raw_data.csv")
MODEL_PATH = os.path.join(BASE_DIR, "storm_model.pkl")


def custom_label(row):
    """
    Apply integrated weather labeling rules:
    1. True thunderstorm (weather_main == "Thunderstorm" or 200 <= weather_id < 300)
    2. Heavy rain treated as thunderstorm-like (weather_main == "Rain" and rain_1h >= 5.0 mm)
    """
    wm = str(row.get("weather_main", ""))
    wid = row.get("weather_id", None)
    
    try:
        wid_int = int(wid) if pd.notna(wid) else None
    except (ValueError, TypeError):
        wid_int = None

    # Rule 1: True thunderstorm
    if wm == "Thunderstorm":
        return 1
    if wid_int is not None and 200 <= wid_int < 300:
        return 1

    # Rule 2: Heavy rain
    try:
        rain = float(row.get("rain_1h", 0.0))
    except (TypeError, ValueError):
        rain = 0.0

    if wm == "Rain" and rain >= 5.0:
        return 1

    # Otherwise: normal
    return 0


def prepare_dataset():
    """Load CSV, apply integrated labels, and build features X and labels y."""
    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(f"Dataset not found at {CSV_PATH}. Please run the collection script first.")

    df = pd.read_csv(CSV_PATH, parse_dates=["time"])

    # Sort by node and time
    df = df.sort_values(["node", "time"]).reset_index(drop=True)

    # Previous values per node
    df["pressure_prev"] = df.groupby("node")["pressure"].shift(1)
    df["humidity_prev"] = df.groupby("node")["humidity"].shift(1)

    # Change features
    df["pressure_change"] = df["pressure"] - df["pressure_prev"]
    df["humidity_change"] = df["humidity"] - df["humidity_prev"]

    # Fill missing change values (first row per node) with 0
    df[["pressure_change", "humidity_change"]] = df[
        ["pressure_change", "humidity_change"]
    ].fillna(0)

    # Automatically update/apply labels to ensure clean training data
    df["label"] = df.apply(custom_label, axis=1)

    # Keep only rows where label exists
    df = df.dropna(subset=["label"])
    df["label"] = df["label"].astype(int)

    feature_cols = [
        "temp",
        "pressure",
        "humidity",
        "wind_speed",
        "cloudiness",
        "rain_1h",
        "pressure_change",
        "humidity_change",
    ]

    X = df[feature_cols]
    y = df["label"]

    print(f"Dataset size: {len(df)} rows")
    print("Label counts:", y.value_counts().to_dict())
    return X, y


def train_model():
    """Train RandomForest Classifier and save the model."""
    X, y = prepare_dataset()

    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42
    )

    # Train Random Forest classifier
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X_train, y_train)

    # Evaluate
    y_pred = clf.predict(X_test)
    print("\nModel performance:")
    print("Accuracy:", accuracy_score(y_test, y_pred))
    print("\nClassification report:\n")
    print(classification_report(y_test, y_pred))

    # Save model
    joblib.dump(clf, MODEL_PATH)
    print(f"\nModel saved to {MODEL_PATH}")


if __name__ == "__main__":
    train_model()
