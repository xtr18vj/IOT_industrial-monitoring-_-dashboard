from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class HealthEvaluation:
    temperature_c: float
    vibration_pct: float
    health_score: float
    status: str
    temperature_penalty: float
    vibration_penalty: float


class HealthEngine:
    @staticmethod
    def _safe_float(value: object) -> float:
        try:
            if value is None:
                return np.nan
            return float(value)
        except (TypeError, ValueError):
            return np.nan

    @staticmethod
    def _piecewise_penalty(value: float, warning: float, critical: float, max_value: float) -> float:
        if np.isnan(value):
            return 100.0
        if value < warning:
            return 0.0
        if value < critical:
            return ((value - warning) / max(critical - warning, 1e-6)) * 40.0
        critical_excess = min(max(value - critical, 0.0), max_value - critical)
        return 40.0 + (critical_excess / max(max_value - critical, 1e-6)) * 60.0

    def evaluate(
        self,
        temperature_c: object,
        vibration_pct: object,
        temp_warning: float = 40.0,
        vibration_warning: float = 70.0,
        temp_critical: float = 60.0,
        vibration_critical: float = 85.0,
    ) -> dict:
        temp = self._safe_float(temperature_c)
        vibration = self._safe_float(vibration_pct)

        if np.isnan(temp) or np.isnan(vibration):
            result = HealthEvaluation(
                temperature_c=temp,
                vibration_pct=vibration,
                health_score=0.0,
                status="SENSOR_FAULT",
                temperature_penalty=100.0,
                vibration_penalty=100.0,
            )
            return result.__dict__

        temp_penalty = self._piecewise_penalty(temp, temp_warning, temp_critical, max_value=100.0)
        vibration_penalty = self._piecewise_penalty(vibration, vibration_warning, vibration_critical, max_value=100.0)

        combined_penalty = (0.55 * temp_penalty) + (0.45 * vibration_penalty)
        health_score = float(np.clip(100.0 - combined_penalty, 0.0, 100.0))

        if temp >= temp_critical or vibration >= vibration_critical:
            status = "CRITICAL"
        elif temp >= temp_warning or vibration >= vibration_warning:
            status = "WARNING"
        else:
            status = "NORMAL"

        result = HealthEvaluation(
            temperature_c=temp,
            vibration_pct=vibration,
            health_score=round(health_score, 2),
            status=status,
            temperature_penalty=round(float(temp_penalty), 2),
            vibration_penalty=round(float(vibration_penalty), 2),
        )
        return result.__dict__


def detect_anomaly(history_df: pd.DataFrame, min_samples: int = 20, z_threshold: float = 2.8) -> dict:
    if history_df.empty or len(history_df) < min_samples:
        return {"detected": False, "reason": "Not enough historical data for anomaly detection."}

    recent = history_df.tail(80).copy()
    if recent.empty:
        return {"detected": False, "reason": "No recent samples available."}

    reasons: list[str] = []
    for col, label in [("temperature_c", "temperature"), ("vibration_pct", "vibration")]:
        series = pd.to_numeric(recent[col], errors="coerce").dropna()
        if len(series) < min_samples:
            continue
        current_value = float(series.iloc[-1])
        mean = float(series.mean())
        std = float(series.std(ddof=0))
        z_score = 0.0 if std == 0 else (current_value - mean) / std
        if abs(z_score) >= z_threshold:
            reasons.append(f"Unusual {label}: z-score {z_score:.2f}")

    if len(recent) >= 2:
        prev = recent.iloc[-2]
        curr = recent.iloc[-1]
        temp_jump = abs(float(curr["temperature_c"]) - float(prev["temperature_c"])) if pd.notna(curr["temperature_c"]) and pd.notna(prev["temperature_c"]) else 0.0
        vib_jump = abs(float(curr["vibration_pct"]) - float(prev["vibration_pct"])) if pd.notna(curr["vibration_pct"]) and pd.notna(prev["vibration_pct"]) else 0.0
        if temp_jump > 12.0:
            reasons.append(f"Rapid temperature jump (+/-{temp_jump:.2f}°C)")
        if vib_jump > 20.0:
            reasons.append(f"Rapid vibration jump (+/-{vib_jump:.2f}%)")

    if reasons:
        return {"detected": True, "reason": "; ".join(reasons)}
    return {"detected": False, "reason": "No abnormal pattern detected in the latest reading."}


def get_maintenance_action(status: str, anomaly_detected: bool) -> str:
    if status == "CRITICAL":
        return "Immediate inspection required. Reduce load, inspect bearings/cooling, and schedule urgent maintenance."
    if status == "WARNING":
        if anomaly_detected:
            return "Run condition-based checks now and plan maintenance in the next shift."
        return "Monitor closely, review lubrication/cooling, and perform preventive checks soon."
    if status == "SENSOR_FAULT":
        return "Validate sensor wiring/calibration and verify data quality before operational decisions."
    if anomaly_detected:
        return "Continue operation with caution and run targeted diagnostics for early fault confirmation."
    return "Machine is operating within expected range. Continue routine preventive maintenance."
