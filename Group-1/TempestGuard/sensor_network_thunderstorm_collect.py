"""
sensor_network_thunderstorm_collect.py

Periodically collects weather data from multiple virtual sensor nodes
(using OpenWeatherMap API) and appends it to thunderstorm_raw_data.csv.

This script directly applies custom labeling rules during collection:
1. True thunderstorm (weather_main == "Thunderstorm" or 200 <= weather_id < 300)
2. Heavy rain treated as thunderstorm-like (weather_main == "Rain" and rain_1h >= 5.0 mm)
"""

import os
import time
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

# -----------------------------
# Configuration
# -----------------------------

API_KEY = os.getenv("OPENWEATHER_API_KEY")
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

# Virtual sensor nodes in Kolkata area
NODES = [
    {"name": "Howrah AC", "lat": 22.6532, "lon": 88.3776},
    {"name": "Howrah Maidan", "lat": 22.5839, "lon": 88.3335},
    {"name": "Burrabazar", "lat": 22.5626, "lon": 88.3630},
    {"name": "NewTown", "lat": 22.5816, "lon": 88.4527},
    {"name": "Barasat", "lat": 22.9810, "lon": 88.4345},
]

# Path Resolution
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_CSV = os.path.join(BASE_DIR, "thunderstorm_raw_data.csv")

# Collection settings
NUM_ITERATIONS = 30          # Number of samples to collect
SLEEP_SECONDS = 60           # Seconds to wait between samples (1 minute)

# -----------------------------
# Helper Functions
# -----------------------------

def fetch_node_data(node):
    """Fetch current weather data for one node from OpenWeatherMap."""
    if not API_KEY:
        raise RuntimeError(
            "OPENWEATHER_API_KEY is missing. Add it to the .env file."
        )

    params = {
        "lat": node["lat"],
        "lon": node["lon"],
        "appid": API_KEY,
        "units": "metric",
    }
    r = requests.get(BASE_URL, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()

    main = data.get("main", {})
    wind = data.get("wind", {})
    clouds = data.get("clouds", {})
    rain = data.get("rain", {})
    weather = data.get("weather", [{}])[0]

    row = {
        "time": pd.Timestamp.utcnow(),
        "node": node["name"],
        "temp": main.get("temp"),
        "pressure": main.get("pressure"),
        "humidity": main.get("humidity"),
        "wind_speed": wind.get("speed"),
        "cloudiness": clouds.get("all"),
        "rain_1h": rain.get("1h", 0.0),
        "weather_main": weather.get("main"),
        "weather_id": weather.get("id"),
    }
    return row


def label_from_weather(weather_main, weather_id, rain_1h=0.0):
    """
    Determine if weather conditions indicate a thunderstorm or high risk.
    Rule 1: True thunderstorm from API codes (2xx range).
    Rule 2: Heavy rain (>= 5.0 mm in last hour) treated as thunderstorm-like.
    """
    try:
        wm = str(weather_main)
        wid_int = int(weather_id) if weather_id is not None else None
        
        # Rule 1: True thunderstorm
        if wm == "Thunderstorm":
            return 1
        if wid_int is not None and 200 <= wid_int < 300:
            return 1
            
        # Rule 2: Heavy rain
        try:
            rain = float(rain_1h) if rain_1h is not None else 0.0
        except (TypeError, ValueError):
            rain = 0.0
            
        if wm == "Rain" and rain >= 5.0:
            return 1
    except Exception:
        pass
    return 0


def load_existing_csv():
    """Load existing CSV if present, else return empty DataFrame."""
    try:
        df = pd.read_csv(DATA_CSV)
        return df
    except FileNotFoundError:
        return pd.DataFrame()


def save_df(df):
    """Save DataFrame to CSV."""
    df.to_csv(DATA_CSV, index=False)
    print(f"Saved {len(df)} total rows to {DATA_CSV}")


def print_label_counts(df):
    """Print count of thunderstorm vs non-thunderstorm rows."""
    if "label" not in df.columns or df.empty:
        print("No label data yet.")
        return
    counts = df["label"].value_counts().to_dict()
    num_storm = counts.get(1, 0)
    num_clear = counts.get(0, 0)
    print(f"Label counts -> Thunderstorm: {num_storm}, No thunderstorm: {num_clear}")


# -----------------------------
# Main Collection Loop
# -----------------------------

def collect_loop():
    """Collect data NUM_ITERATIONS times and append to CSV."""
    df_all = load_existing_csv()
    print(f"Starting collection. Existing rows in CSV: {len(df_all)}")

    for i in range(NUM_ITERATIONS):
        print(f"\nIteration {i + 1} of {NUM_ITERATIONS}")
        rows = []

        for node in NODES:
            try:
                d = fetch_node_data(node)
                # Compute integrated labels
                d["label"] = label_from_weather(d["weather_main"], d["weather_id"], d["rain_1h"])
                rows.append(d)
                print(f"  Collected {node['name']}: "
                      f"temp={d['temp']}°C, press={d['pressure']} hPa, "
                      f"cond={d['weather_main']}, rain={d['rain_1h']}mm, label={d['label']}")
            except Exception as e:
                print(f"  Error fetching {node['name']}: {e}")

        if rows:
            df_batch = pd.DataFrame(rows)
            df_all = pd.concat([df_all, df_batch], ignore_index=True)
            save_df(df_all)
            print_label_counts(df_all)
        else:
            print("No data collected this iteration.")

        if i < NUM_ITERATIONS - 1:
            print(f"Sleeping for {SLEEP_SECONDS} seconds...")
            time.sleep(SLEEP_SECONDS)

    print("\nCollection loop finished.")
    print_label_counts(df_all)


if __name__ == "__main__":
    collect_loop()
