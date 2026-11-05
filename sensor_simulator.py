from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ModeProfile:
    target_temp: float
    target_vibration: float
    temp_noise: float
    vibration_noise: float


class SensorSimulator:
    """
    Simulates machine sensor values for temperature and vibration.
    This class is intentionally isolated so serial/IoT hardware input can replace it later.
    """

    def __init__(self, seed: int | None = None) -> None:
        self.rng = np.random.default_rng(seed)
        self.temperature_c = 34.0
        self.vibration_pct = 42.0

        self.mode_profiles = {
            "Normal": ModeProfile(36.0, 48.0, 0.7, 2.4),
            "Idle": ModeProfile(31.0, 30.0, 0.5, 1.8),
            "High Load": ModeProfile(44.0, 66.0, 1.1, 3.3),
        }

    @staticmethod
    def _bounded(value: float, low: float, high: float) -> float:
        return float(min(max(value, low), high))

    def _drift(self, current: float, target: float, noise_scale: float, pull: float = 0.15) -> float:
        noise = self.rng.normal(0.0, noise_scale)
        return current + (target - current) * pull + noise

    def generate_reading(self, operating_mode: str = "Normal", disturbance_mode: str = "None") -> dict:
        profile = self.mode_profiles.get(operating_mode, self.mode_profiles["Normal"])

        self.temperature_c = self._drift(self.temperature_c, profile.target_temp, profile.temp_noise)
        self.vibration_pct = self._drift(self.vibration_pct, profile.target_vibration, profile.vibration_noise)

        if disturbance_mode == "Overheating":
            self.temperature_c += self.rng.uniform(8.0, 16.0)
        elif disturbance_mode == "Excessive Vibration":
            self.vibration_pct += self.rng.uniform(14.0, 25.0)
        elif disturbance_mode == "Combined Stress":
            self.temperature_c += self.rng.uniform(10.0, 20.0)
            self.vibration_pct += self.rng.uniform(12.0, 24.0)

        temperature = self._bounded(self.temperature_c, 10.0, 110.0)
        vibration = self._bounded(self.vibration_pct, 0.0, 100.0)

        if disturbance_mode == "Sensor Fault":
            fault_case = self.rng.choice(["temp_nan", "vibration_nan", "both_nan"], p=[0.45, 0.45, 0.10])
            if fault_case in {"temp_nan", "both_nan"}:
                temperature = np.nan
            if fault_case in {"vibration_nan", "both_nan"}:
                vibration = np.nan

        return {
            "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
            "temperature_c": round(float(temperature), 2) if np.isfinite(temperature) else np.nan,
            "vibration_pct": round(float(vibration), 2) if np.isfinite(vibration) else np.nan,
        }
