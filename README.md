# Industrial IoT – Smart Machine Health Monitoring & Predictive Maintenance

A professional Streamlit dashboard that simulates industrial machine sensor data, evaluates machine health, generates alerts, and highlights anomaly-based maintenance insights.

> **Important:** This dashboard currently uses **Python-based simulated data**. It does **not** claim live connectivity with Tinkercad/Arduino yet.

---

## 1) Project Overview

Industrial machines often fail because early warning signals (temperature rise, excessive vibration) are missed. This project demonstrates a practical monitoring dashboard that tracks these indicators in real time and supports preventive action before severe failure risk.

This project is designed for internship submissions, technical interviews, GitHub showcases, and LinkedIn demonstrations.

---

## 2) Problem Statement

In many industrial setups:
- Operators monitor machine conditions manually.
- Alerting is delayed or inconsistent.
- Maintenance is reactive instead of predictive.

This solution addresses the gap with a clean and explainable Industrial IoT dashboard.

---

## 3) Objectives

- Simulate realistic machine sensor readings (temperature + vibration).
- Evaluate machine operating condition with an explainable health score.
- Trigger NORMAL / WARNING / CRITICAL alerts with event history.
- Detect unusual behavior using statistical anomaly detection.
- Present all information in a professional dark-themed dashboard.

---

## 4) Hardware Simulation Context (Tinkercad)

You already built a separate Arduino UNO simulation with:
- TMP36 on A0 (temperature)
- Potentiometer on A1 (vibration percentage simulation)
- 16x2 LCD
- Green LED (normal)
- Red LED + buzzer (abnormal)

Current software phase:
- Tinkercad and Streamlit run independently.
- Streamlit generates internal simulated values.
- Code is modular so serial integration (Arduino/ESP32) can be added later.

---

## 5) Software Architecture

```text
industrial-iot-monitoring/
│
├── app.py                 # Streamlit UI and orchestration
├── sensor_simulator.py    # Realistic sensor data generator
├── health_engine.py       # Health scoring + anomaly logic
├── alert_manager.py       # Alert deduplication and history
├── requirements.txt       # Dependencies
├── README.md              # Documentation
└── data/                  # Optional data artifacts
```

### Module Responsibilities

- **sensor_simulator.py**
  - Simulates temperature and vibration signals
  - Supports operating modes (`Idle`, `Normal`, `High Load`)
  - Supports abnormal scenarios (`Overheating`, `Excessive Vibration`, `Combined Stress`, `Sensor Fault`)

- **health_engine.py**
  - Cleans invalid values
  - Computes explainable 0–100 health score
  - Assigns machine status: `NORMAL`, `WARNING`, `CRITICAL`, `SENSOR_FAULT`
  - Detects anomalies using z-score and rapid change checks
  - Suggests maintenance actions

- **alert_manager.py**
  - Creates timestamped alerts
  - Prevents duplicate alert spam with state transition + cooldown logic
  - Stores alert history table

- **app.py**
  - Dashboard UI, controls, KPI cards, charts, tables, CSV export
  - Session state management for continuous in-session history

---

## 6) Technology Stack

- Python
- Streamlit
- Pandas
- NumPy
- Plotly
- Scikit-learn (included for future ML upgrades)

---

## 7) Features

- Premium dark industrial dashboard
- Real-time simulated readings with timestamped history
- KPI cards:
  - Current Temperature (°C)
  - Vibration Level (%)
  - Machine Health Score (%)
  - Machine Operating Status
- Interactive Plotly trend charts:
  - Temperature over time
  - Vibration over time
  - Health score over time
- Explainable health score logic section
- Alerting system:
  - NORMAL / WARNING / CRITICAL
  - Alert event table with timestamp and sensor values
- Machine status panel:
  - Running/Paused state
  - Current condition
  - Warning and critical counts
  - Suggested maintenance action
- Predictive maintenance insight:
  - Statistical anomaly detection
  - Reason for anomaly
  - Recommended action
- Recent data table with CSV export
- Sidebar controls:
  - Start/Pause simulation
  - Threshold sliders
  - Simulation speed
  - Operating mode
  - Abnormal scenario trigger
  - Session reset

---

## 8) Installation

### Prerequisites
- Python 3.10+ recommended
- pip

### Steps

```bash
# 1) Go to project directory
cd industrial-iot-monitoring

# 2) (Optional) create virtual environment
python -m venv .venv

# 3) Activate environment
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# 4) Install dependencies
pip install -r requirements.txt
```

---

## 9) Run the Dashboard

```bash
streamlit run app.py
```

Then open the local URL shown in terminal (usually `http://localhost:8501`).

---

## 10) Usage Notes

1. Use **Start/Pause Simulation** to control updates.
2. Change machine mode (`Idle`, `Normal`, `High Load`) to see behavior shifts.
3. Trigger abnormal scenarios to demonstrate alerting:
   - Overheating
   - Excessive Vibration
   - Combined Stress
   - Sensor Fault
4. Adjust warning/critical thresholds and simulation speed from sidebar.
5. Export readings via CSV download button.

---

## 11) Screenshots

Add screenshots here after running locally:

- `assets/dashboard-overview.png`
- `assets/alerts-and-anomalies.png`
- `assets/sensor-trends.png`

---

## 12) Reliability Notes

- Handles invalid/missing sensor values (`SENSOR_FAULT` state)
- Prevents duplicate alert floods on every refresh
- Maintains sensor history in Streamlit session state
- Uses modular architecture for easier testing and hardware integration

---

## 13) Future Scope

- Live serial integration with Arduino/ESP32
- MQTT/OPC-UA/Modbus industrial protocol integration
- Persist data to PostgreSQL/InfluxDB
- Advanced anomaly/fault classification models
- Multi-machine fleet view
- Role-based access and notification channels (email/SMS/Teams)

---

## 14) Disclaimer

This project demonstrates explainable condition monitoring and anomaly indication.  
It does **not** claim exact failure date prediction.
