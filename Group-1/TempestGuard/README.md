# TempestGuard

Thunderstorm Prediction Using Virtual Weather Sensor Nodes and Machine Learning

## Project Description

TempestGuard is a software-defined thunderstorm prediction system that uses distributed virtual sensor nodes instead of physical weather stations. The system fetches live weather data from the OpenWeatherMap API for five fixed locations across the Kolkata metropolitan area. Each fetch is stored as a timestamped row in a local CSV file.

Once enough readings are collected, a training script engineers two temporal delta features from the data: the change in barometric pressure and the change in humidity between consecutive readings for the same node. A Random Forest classifier is then trained on this labeled dataset. The trained model is served through a Flask web dashboard that shows each node on an interactive Leaflet map, displays current weather metrics, and uses the Haversine formula to recommend the nearest safe node whenever storm risk is detected at a location.

## Problem Statement

Thunderstorms develop rapidly and can cause serious hazards within minutes. Deploying physical weather stations at the local level is expensive. Standard weather apps report broad regional trends and offer no localized micro-climate forecasting, nor do they give actionable guidance like identifying a nearby safe area when conditions deteriorate.

## Objectives

- Collect live weather observations from multiple virtual sensor nodes using the OpenWeatherMap API.
- Engineer temporal delta features that capture short-term atmospheric changes, specifically pressure change and humidity change between readings.
- Automatically classify thunderstorm versus non-thunderstorm conditions during data collection and use that labeled data to train a machine learning model.
- Deploy model predictions through a Flask dashboard with an interactive Leaflet map.
- Calculate and display the nearest safe sensor node for any location flagged as a storm risk, using the Haversine formula.

## Technologies Used

- Python 3.x, Flask
- Pandas, NumPy
- Scikit-Learn (Random Forest Classifier), Joblib
- Requests (OpenWeatherMap API)
- HTML5, CSS3, JavaScript (ES6)
- Leaflet.js, OpenStreetMap (CartoDB Dark basemap)

## Machine Learning Model

The prediction engine uses a Random Forest Classifier with 100 estimators, trained on a 70/30 train-test split. Random Forest was chosen because it handles mixed feature scales well, captures non-linear relationships, and produces predictions with very low latency.

The two differential features, pressure change and humidity change, carry the most predictive weight because sudden drops in pressure and rapid humidity rises are the primary atmospheric indicators of approaching thunderstorm onset.

## Dataset

The dataset is stored in `thunderstorm_raw_data.csv`. Each row is one weather observation from one node at a specific UTC timestamp.

| Column | Description |
|---|---|
| temp | Air temperature in degrees Celsius |
| pressure | Barometric pressure at sea level in hPa |
| humidity | Relative humidity as a percentage |
| wind_speed | Wind speed in metres per second |
| cloudiness | Cloud coverage as a percentage |
| rain_1h | Rainfall in the past hour in millimetres |
| pressure_change | Pressure difference from the previous reading for the same node |
| humidity_change | Humidity difference from the previous reading for the same node |
| label | 1 for storm risk, 0 for safe conditions |

## Installation

**Requirements:** Python 3.8 or above. An OpenWeatherMap API key (free tier available at https://openweathermap.org/).

**1. Clone the repository**

```bash
git clone https://github.com/pmohata34/TempestGuard.git
cd TempestGuard
```

**2. Create and activate a virtual environment**

On Windows:
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

On macOS or Linux:
```bash
python -m venv .venv
source .venv/bin/activate
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Set your API key**

Copy `.env.example` to `.env`, then replace `your_api_key_here` with your OpenWeatherMap API key. The collector loads `.env` automatically, and `.env` is ignored by Git.

Alternatively, set the environment variable directly.

On Windows:
```powershell
$env:OPENWEATHER_API_KEY="your_api_key_here"
```

On macOS or Linux:
```bash
export OPENWEATHER_API_KEY="your_api_key_here"
```

## How to Run

Run the three scripts in order.

**Step 1: Collect live data**

Fetches weather observations for all five nodes and appends them to the CSV file. By default it runs 30 iterations with a 60-second pause between each, so this takes roughly 30 minutes to build a meaningful dataset.

```bash
python sensor_network_thunderstorm_collect.py
```

**Step 2: Train the model**

Reads the collected data, engineers the change features, applies automatic labeling, trains the Random Forest model, and saves it as `storm_model.pkl`.

```bash
python sensor_network_thunderstorm_ml.py
```

**Step 3: Launch the dashboard**

Starts the Flask application on localhost port 5000.

```bash
python app.py
```

Open a browser and go to `http://127.0.0.1:5000/`

## Expected Output

After running the collection script you will see something like:

```
Starting collection. Existing rows in CSV: 265
Iteration 1 of 30
  Collected Howrah AC: temp=30.2C, press=1008 hPa, cond=Rain, rain=0.0mm, label=0
  Collected Newtown: temp=29.8C, press=1007 hPa, cond=Thunderstorm, rain=2.3mm, label=1
Saved 270 total rows to thunderstorm_raw_data.csv
Label counts -> Thunderstorm: 8, No thunderstorm: 262
```

After training:

```
Dataset size: 265 rows
Label counts: {0: 257, 1: 8}
Accuracy: 1.0
Model saved to storm_model.pkl
```

The dashboard shows an interactive map with green circles for safe nodes and red circles for storm-risk nodes. Any at-risk node displays a recommendation card naming the nearest safe location and its distance, for example: "Thunderstorm risk detected. Nearest safe node: Newtown (3.2 km away)."

## Future Scope

- Move from virtual API-based nodes to physical ESP32 microcontrollers with BMP280 pressure and DHT22 humidity sensors for real hardware deployment.
- Add rolling average windows and multi-step trend statistics to capture longer atmospheric patterns before storm onset.
- Replace batch collection with a continuous stream processor so features update in real time.
- Add SMS or push notification alerts tied to evacuation guidance when a node crosses the storm-risk threshold.

## Contributors

- Pranjal Mohata (Lead Developer)
- Anuradha Banerjee (Research Internship Mentor)