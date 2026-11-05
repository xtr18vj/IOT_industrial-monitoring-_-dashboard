from __future__ import annotations

import time
from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st

from alert_manager import AlertManager
from health_engine import HealthEngine, detect_anomaly, get_maintenance_action
from sensor_simulator import SensorSimulator


st.set_page_config(
    page_title="Smart Machine Health Monitoring",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)


def inject_theme() -> None:
    st.markdown(
        """
        <style>
            :root {
                --bg-primary: #0b1220;
                --bg-secondary: #121b2f;
                --text-primary: #f3f6ff;
                --text-muted: #9aa9c7;
                --normal: #2fd47a;
                --warning: #f0b429;
                --critical: #f25f5c;
                --border: #273550;
            }
            .stApp {
                background: radial-gradient(circle at top right, #1a2642 0%, var(--bg-primary) 50%);
                color: var(--text-primary);
            }
            .kpi-card {
                background: linear-gradient(145deg, #131d33 0%, #0f1729 100%);
                border: 1px solid var(--border);
                border-radius: 12px;
                padding: 14px 16px;
                min-height: 110px;
            }
            .kpi-label {
                color: var(--text-muted);
                font-size: 0.88rem;
                margin-bottom: 8px;
            }
            .kpi-value {
                font-size: 1.85rem;
                font-weight: 700;
                line-height: 1.2;
            }
            .status-pill {
                display: inline-block;
                padding: 6px 12px;
                border-radius: 999px;
                font-weight: 600;
                font-size: 0.85rem;
                border: 1px solid transparent;
            }
            .status-normal { color: var(--normal); background: rgba(47, 212, 122, 0.1); border-color: rgba(47, 212, 122, 0.4); }
            .status-warning { color: var(--warning); background: rgba(240, 180, 41, 0.12); border-color: rgba(240, 180, 41, 0.4); }
            .status-critical { color: var(--critical); background: rgba(242, 95, 92, 0.12); border-color: rgba(242, 95, 92, 0.4); }
            .status-fault { color: #f2c94c; background: rgba(242, 201, 76, 0.15); border-color: rgba(242, 201, 76, 0.45); }
            .section-title {
                margin-top: 10px;
                margin-bottom: 4px;
                font-weight: 700;
                font-size: 1.05rem;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def status_class(status: str) -> str:
    if status == "CRITICAL":
        return "status-critical"
    if status == "WARNING":
        return "status-warning"
    if status == "SENSOR_FAULT":
        return "status-fault"
    return "status-normal"


def init_state() -> None:
    if "simulator" not in st.session_state:
        st.session_state.simulator = SensorSimulator(seed=42)
    if "health_engine" not in st.session_state:
        st.session_state.health_engine = HealthEngine()
    if "alerts" not in st.session_state:
        st.session_state.alerts = AlertManager(cooldown_seconds=120)
    if "history" not in st.session_state:
        st.session_state.history = pd.DataFrame(
            columns=[
                "timestamp",
                "temperature_c",
                "vibration_pct",
                "health_score",
                "status",
                "anomaly_detected",
                "anomaly_reason",
                "maintenance_action",
            ]
        )
    if "running" not in st.session_state:
        st.session_state.running = True


def render_header(latest_row: pd.Series | None) -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    current_status = "NORMAL" if latest_row is None else str(latest_row["status"])
    st.markdown("## Smart Machine Health Monitoring")
    col1, col2 = st.columns([2, 1])
    with col1:
        st.caption("Industrial IoT Predictive Maintenance System")
    with col2:
        st.markdown(f"**Current Time:** {now}")
    pill_class = status_class(current_status)
    st.markdown(
        f'<span class="status-pill {pill_class}">Machine Status: {current_status}</span>',
        unsafe_allow_html=True,
    )


def render_kpi_cards(latest_row: pd.Series | None) -> None:
    if latest_row is None:
        temperature = "N/A"
        vibration = "N/A"
        health_score = "N/A"
        machine_state = "NO_DATA"
    else:
        temperature = f"{latest_row['temperature_c']:.2f} °C"
        vibration = f"{latest_row['vibration_pct']:.2f} %"
        health_score = f"{latest_row['health_score']:.1f} %"
        machine_state = str(latest_row["status"])

    c1, c2, c3, c4 = st.columns(4)
    cards = [
        (c1, "Current Temperature", temperature),
        (c2, "Vibration Level", vibration),
        (c3, "Machine Health Score", health_score),
        (c4, "Machine Operating Status", machine_state),
    ]
    for col, label, value in cards:
        with col:
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-label">{label}</div>
                    <div class="kpi-value">{value}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def add_simulated_point(
    operating_mode: str,
    disturbance_mode: str,
    temp_warning: float,
    vibration_warning: float,
    temp_critical: float,
    vibration_critical: float,
    max_rows: int,
) -> None:
    reading = st.session_state.simulator.generate_reading(
        operating_mode=operating_mode,
        disturbance_mode=disturbance_mode,
    )
    evaluated = st.session_state.health_engine.evaluate(
        temperature_c=reading.get("temperature_c"),
        vibration_pct=reading.get("vibration_pct"),
        temp_warning=temp_warning,
        vibration_warning=vibration_warning,
        temp_critical=temp_critical,
        vibration_critical=vibration_critical,
    )

    row = {
        "timestamp": reading.get("timestamp"),
        "temperature_c": evaluated["temperature_c"],
        "vibration_pct": evaluated["vibration_pct"],
        "health_score": evaluated["health_score"],
        "status": evaluated["status"],
        "anomaly_detected": False,
        "anomaly_reason": "",
        "maintenance_action": "",
    }

    st.session_state.history = pd.concat(
        [st.session_state.history, pd.DataFrame([row])], ignore_index=True
    ).tail(max_rows)

    anomaly = detect_anomaly(st.session_state.history)
    action = get_maintenance_action(evaluated["status"], anomaly["detected"])
    st.session_state.history.iloc[-1, st.session_state.history.columns.get_loc("anomaly_detected")] = anomaly[
        "detected"
    ]
    st.session_state.history.iloc[-1, st.session_state.history.columns.get_loc("anomaly_reason")] = anomaly[
        "reason"
    ]
    st.session_state.history.iloc[-1, st.session_state.history.columns.get_loc("maintenance_action")] = action

    st.session_state.alerts.process_reading(
        timestamp=row["timestamp"],
        status=evaluated["status"],
        temperature_c=evaluated["temperature_c"],
        vibration_pct=evaluated["vibration_pct"],
        health_score=evaluated["health_score"],
        anomaly_detected=anomaly["detected"],
        anomaly_reason=anomaly["reason"],
    )


def build_line_chart(df: pd.DataFrame, y_col: str, title: str, y_title: str):
    fig = px.line(df, x="timestamp", y=y_col, markers=False, template="plotly_dark", title=title)
    fig.update_layout(
        margin=dict(l=20, r=20, t=45, b=25),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", y=-0.2),
    )
    fig.update_traces(line=dict(width=3))
    fig.update_yaxes(title_text=y_title)
    fig.update_xaxes(title_text="Timestamp")
    return fig


def render_sensor_monitoring(df: pd.DataFrame) -> None:
    st.markdown('<div class="section-title">Sensor Monitoring</div>', unsafe_allow_html=True)
    if df.empty:
        st.info("No readings yet. Start the simulation to populate the charts.")
        return
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(
            build_line_chart(df, "temperature_c", "Temperature Trend", "Temperature (°C)"),
            use_container_width=True,
        )
    with c2:
        st.plotly_chart(
            build_line_chart(df, "vibration_pct", "Vibration Trend", "Vibration (%)"),
            use_container_width=True,
        )
    st.plotly_chart(
        build_line_chart(df, "health_score", "Machine Health Trend", "Health Score (%)"),
        use_container_width=True,
    )


def render_health_logic(temp_warning: float, vibration_warning: float, temp_critical: float, vibration_critical: float):
    with st.expander("How health score is calculated"):
        st.markdown(
            f"""
            - **Temperature Zones:** normal `< {temp_warning:.1f}°C`, warning `{temp_warning:.1f}–{temp_critical:.1f}°C`, critical `> {temp_critical:.1f}°C`
            - **Vibration Zones:** normal `< {vibration_warning:.1f}%`, warning `{vibration_warning:.1f}–{vibration_critical:.1f}%`, critical `> {vibration_critical:.1f}%`
            - A penalty is applied to temperature and vibration based on severity.
            - Final health score = `100 - (0.55 × temperature_penalty + 0.45 × vibration_penalty)`.
            - Output is clipped to **0–100**.
            """
        )


def render_alerts_and_status(latest_row: pd.Series | None) -> None:
    st.markdown('<div class="section-title">Alerts & Machine Status</div>', unsafe_allow_html=True)
    alerts_df = st.session_state.alerts.get_alert_history_df()

    warning_count = int((alerts_df["severity"] == "WARNING").sum()) if not alerts_df.empty else 0
    critical_count = int((alerts_df["severity"] == "CRITICAL").sum()) if not alerts_df.empty else 0

    running_state = "RUNNING" if st.session_state.running else "PAUSED"
    operating_condition = "NO_DATA" if latest_row is None else str(latest_row["status"])
    suggested_action = (
        "Start simulation to evaluate machine health."
        if latest_row is None
        else str(latest_row["maintenance_action"])
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Machine State", running_state)
    c2.metric("Operating Condition", operating_condition)
    c3.metric("Warnings", warning_count)
    c4.metric("Critical Alerts", critical_count)
    st.info(f"**Suggested Maintenance Action:** {suggested_action}")

    if alerts_df.empty:
        st.success("No alerts generated yet.")
    else:
        latest_alert = alerts_df.iloc[0]
        sev = latest_alert["severity"]
        alert_text = (
            f"[{latest_alert['timestamp']}] {sev} | "
            f"Temp: {latest_alert['temperature_c']}°C | "
            f"Vibration: {latest_alert['vibration_pct']}% | "
            f"Health: {latest_alert['health_score']}% | "
            f"{latest_alert['message']}"
        )
        if sev == "CRITICAL":
            st.error(alert_text)
        elif sev == "WARNING":
            st.warning(alert_text)
        else:
            st.success(alert_text)
        st.dataframe(alerts_df, use_container_width=True, hide_index=True)


def render_anomaly_section(df: pd.DataFrame) -> None:
    st.markdown('<div class="section-title">Predictive Maintenance (Anomaly Insights)</div>', unsafe_allow_html=True)
    if df.empty:
        st.info("No data available yet for anomaly analysis.")
        return

    latest = df.iloc[-1]
    if bool(latest["anomaly_detected"]):
        st.warning(
            f"Anomaly detected at {latest['timestamp']}: {latest['anomaly_reason']}. "
            f"Recommended action: {latest['maintenance_action']}"
        )
    else:
        st.success("No anomaly detected in the latest reading.")

    anomaly_rows = df[df["anomaly_detected"] == True]  # noqa: E712
    if anomaly_rows.empty:
        st.caption("No anomaly events recorded in this session.")
    else:
        st.dataframe(
            anomaly_rows[
                [
                    "timestamp",
                    "temperature_c",
                    "vibration_pct",
                    "health_score",
                    "anomaly_reason",
                    "maintenance_action",
                ]
            ].tail(20),
            use_container_width=True,
            hide_index=True,
        )


def render_data_table(df: pd.DataFrame) -> None:
    st.markdown('<div class="section-title">Recent Sensor Data</div>', unsafe_allow_html=True)
    if df.empty:
        st.info("No sensor readings available.")
        return
    table = df.tail(200).copy()
    st.dataframe(table, use_container_width=True, hide_index=True)
    csv_bytes = table.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download Recent Readings (CSV)",
        data=csv_bytes,
        file_name=f"sensor_readings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
    )


def main() -> None:
    inject_theme()
    init_state()

    with st.sidebar:
        st.header("Simulation Controls")
        if st.button("Pause Simulation" if st.session_state.running else "Start Simulation", use_container_width=True):
            st.session_state.running = not st.session_state.running

        operating_mode = st.selectbox(
            "Machine Operating Mode",
            options=["Normal", "Idle", "High Load"],
            index=0,
        )
        disturbance_mode = st.selectbox(
            "Abnormal Scenario",
            options=["None", "Overheating", "Excessive Vibration", "Combined Stress", "Sensor Fault"],
            index=0,
        )
        temp_warning = st.slider("Temperature Warning Threshold (°C)", 30.0, 55.0, 40.0, 0.5)
        vibration_warning = st.slider("Vibration Warning Threshold (%)", 55.0, 80.0, 70.0, 1.0)
        temp_critical = st.slider("Temperature Critical Threshold (°C)", 50.0, 85.0, 60.0, 0.5)
        vibration_critical = st.slider("Vibration Critical Threshold (%)", 75.0, 99.0, 85.0, 1.0)
        speed = st.slider("Simulation Speed (seconds/update)", 0.5, 5.0, 1.5, 0.5)
        history_limit = st.slider("Maximum Stored Readings", 100, 3000, 800, 50)

        if st.button("Reset Session Data", use_container_width=True):
            st.session_state.history = st.session_state.history.iloc[0:0]
            st.session_state.alerts.reset()
            st.success("Session data reset.")

    if st.session_state.running:
        add_simulated_point(
            operating_mode=operating_mode,
            disturbance_mode=disturbance_mode,
            temp_warning=temp_warning,
            vibration_warning=vibration_warning,
            temp_critical=temp_critical,
            vibration_critical=vibration_critical,
            max_rows=history_limit,
        )

    history_df = st.session_state.history.copy()
    latest = None if history_df.empty else history_df.iloc[-1]

    render_header(latest)
    render_kpi_cards(latest)
    render_health_logic(temp_warning, vibration_warning, temp_critical, vibration_critical)
    render_sensor_monitoring(history_df)
    render_alerts_and_status(latest)
    render_anomaly_section(history_df)
    render_data_table(history_df)

    st.caption(
        "Data shown here is simulated in Python. Tinkercad hardware and this dashboard are intentionally independent in this phase."
    )

    if st.session_state.running:
        time.sleep(speed)
        st.rerun()


if __name__ == "__main__":
    main()
