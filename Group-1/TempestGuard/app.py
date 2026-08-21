import os
import math
import joblib
import pandas as pd
from flask import Flask, render_template

# Initialize Flask App pointing to the src/ directory for assets
app = Flask(__name__, template_folder="src/templates", static_folder="src/static")

# Paths inside the root directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "thunderstorm_raw_data.csv")
MODEL_PATH = os.path.join(BASE_DIR, "storm_model.pkl")

# Node coordinates for geographic mapping on dashboard
NODES_COORDS = {
    "Howrah AC": {"lat": 22.5958, "lon": 88.2636},
    "Howrah Maidan": {"lat": 22.5797, "lon": 88.3294},
    "Burrabazar": {"lat": 22.5760, "lon": 88.3574},
    "NewTown": {"lat": 22.5752, "lon": 88.4796},
    "Barasat": {"lat": 22.7215, "lon": 88.4819},
}

FEATURE_COLS = [
    "temp", "pressure", "humidity", "wind_speed",
    "cloudiness", "rain_1h", "pressure_change", "humidity_change",
]


def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance between two points on the Earth
    using their latitudes and longitudes in decimal degrees.
    """
    r = 6371.0  # Earth's radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return r * c


def load_latest_data():
    """
    Load weather data from CSV, sort by time, calculate differential pressure/humidity
    features, and extract the latest reading for each sensor node.
    """
    if not os.path.exists(CSV_PATH):
        return pd.DataFrame()

    df = pd.read_csv(CSV_PATH, parse_dates=["time"])
    df = df.sort_values(["node", "time"]).reset_index(drop=True)

    # Calculate differences over time per node
    df["pressure_prev"] = df.groupby("node")["pressure"].shift(1)
    df["humidity_prev"] = df.groupby("node")["humidity"].shift(1)

    df["pressure_change"] = (df["pressure"] - df["pressure_prev"]).fillna(0)
    df["humidity_change"] = (df["humidity"] - df["humidity_prev"]).fillna(0)

    # Return only the most recent sample for each node
    return df.groupby("node").tail(1).copy()


@app.route("/")
def index():
    """
    Dashboard route. Loads latest weather data, queries the ML model
    for predictions, calculates safe routing options, and renders the template.
    """
    latest = load_latest_data()
    if latest.empty:
        return f"No weather data found. Please run the collector script first: `python sensor_network_thunderstorm_collect.py`"

    if not os.path.exists(MODEL_PATH):
        return f"Model file not found. Please train the ML model first: `python sensor_network_thunderstorm_ml.py`"

    # Load trained RandomForest model
    model = joblib.load(MODEL_PATH)
    preds = model.predict(latest[FEATURE_COLS])

    rows = []
    active_threats = 0
    safe_count = 0

    for (_, row), pred in zip(latest.iterrows(), preds):
        node_name = row["node"]
        coords = NODES_COORDS.get(node_name, {"lat": 0.0, "lon": 0.0})
        is_safe = bool(pred == 0)

        if is_safe:
            safe_count += 1
        else:
            active_threats += 1

        rows.append(
            {
                "node": node_name,
                "lat": coords["lat"],
                "lon": coords["lon"],
                "temp": round(float(row["temp"]), 2),
                "pressure": int(round(float(row["pressure"]))),
                "humidity": int(round(float(row["humidity"]))),
                "wind_speed": round(float(row["wind_speed"]), 2),
                "cloudiness": int(round(float(row["cloudiness"]))),
                "rain_1h": round(float(row["rain_1h"]), 2),
                "risk": "No Thunderstorm" if is_safe else "Thunderstorm Risk",
                "is_safe": is_safe,
                "nearest_safe_node": None,
                "nearest_safe_dist": None,
            }
        )

    # Calculate the nearest safe place for nodes marked at risk
    for target in rows:
        if not target["is_safe"]:
            best = None
            best_dist = float("inf")

            for candidate in rows:
                if candidate["is_safe"]:
                    dist = haversine_distance(
                        target["lat"],
                        target["lon"],
                        candidate["lat"],
                        candidate["lon"],
                    )
                    if dist < best_dist:
                        best_dist = dist
                        best = candidate

            if best:
                target["nearest_safe_node"] = best["node"]
                target["nearest_safe_dist"] = round(best_dist, 2)

    # Center map based on mean coordinates of nodes
    center_lat = sum(r["lat"] for r in rows) / len(rows)
    center_lon = sum(r["lon"] for r in rows) / len(rows)

    return render_template(
        "dashboard.html",
        rows=rows,
        active_threats=active_threats,
        safe_count=safe_count,
        center_lat=center_lat,
        center_lon=center_lon,
    )


if __name__ == "__main__":
    app.run(debug=True)
