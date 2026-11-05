from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta

import pandas as pd


@dataclass
class AlertRecord:
    timestamp: str
    severity: str
    message: str
    temperature_c: float
    vibration_pct: float
    health_score: float
    anomaly_detected: bool
    anomaly_reason: str


class AlertManager:
    def __init__(self, cooldown_seconds: int = 120) -> None:
        self.cooldown = timedelta(seconds=cooldown_seconds)
        self._alerts: list[AlertRecord] = []
        self._last_severity: str | None = None
        self._last_alert_at: datetime | None = None

    @staticmethod
    def _build_message(severity: str, anomaly_detected: bool) -> str:
        if severity == "CRITICAL":
            if anomaly_detected:
                return "Critical thresholds breached and anomaly pattern detected."
            return "Critical threshold breached. Immediate action required."
        if severity == "WARNING":
            return "Warning threshold exceeded. Investigate operating conditions."
        return "Machine back to normal operating range."

    @staticmethod
    def _severity_from_status(status: str) -> str:
        if status == "CRITICAL":
            return "CRITICAL"
        if status in {"WARNING", "SENSOR_FAULT"}:
            return "WARNING"
        return "NORMAL"

    def process_reading(
        self,
        timestamp: str,
        status: str,
        temperature_c: float,
        vibration_pct: float,
        health_score: float,
        anomaly_detected: bool,
        anomaly_reason: str,
    ) -> AlertRecord | None:
        severity = self._severity_from_status(status)
        current_ts = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")

        should_create = False
        if self._last_severity is None:
            should_create = True
        elif severity != self._last_severity:
            should_create = True
        elif severity in {"WARNING", "CRITICAL"} and self._last_alert_at is not None:
            should_create = (current_ts - self._last_alert_at) >= self.cooldown

        self._last_severity = severity

        if not should_create:
            return None

        record = AlertRecord(
            timestamp=timestamp,
            severity=severity,
            message=self._build_message(severity, anomaly_detected),
            temperature_c=round(float(temperature_c), 2) if pd.notna(temperature_c) else float("nan"),
            vibration_pct=round(float(vibration_pct), 2) if pd.notna(vibration_pct) else float("nan"),
            health_score=round(float(health_score), 2) if pd.notna(health_score) else float("nan"),
            anomaly_detected=bool(anomaly_detected),
            anomaly_reason=anomaly_reason,
        )
        self._alerts.insert(0, record)
        self._last_alert_at = current_ts
        return record

    def get_alert_history_df(self) -> pd.DataFrame:
        if not self._alerts:
            return pd.DataFrame(
                columns=[
                    "timestamp",
                    "severity",
                    "message",
                    "temperature_c",
                    "vibration_pct",
                    "health_score",
                    "anomaly_detected",
                    "anomaly_reason",
                ]
            )
        return pd.DataFrame([asdict(record) for record in self._alerts])

    def reset(self) -> None:
        self._alerts = []
        self._last_severity = None
        self._last_alert_at = None
