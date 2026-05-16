"""Performance metrics for water level control simulations."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd

from water_level_control.simulation import SimulationResult


@dataclass(frozen=True)
class PerformanceMetrics:
    """Compact set of control performance indicators."""

    controller: str
    overshoot_m: float
    overshoot_percent: float
    settling_time_s: float
    steady_state_error_m: float
    mean_absolute_error_m: float
    pump_energy_kwh: float
    pumped_volume_m3: float
    max_pump_command_percent: float


def calculate_metrics(
    result: SimulationResult,
    *,
    settling_band_m: float = 0.03,
    steady_state_window_s: float = 180.0,
    pump_power_kw: float = 1.5,
) -> PerformanceMetrics:
    """Calculate performance indicators for one simulation result.

    ``pump_energy_kwh`` is estimated from a normalized pump command and a
    nominal electrical pump power. This is intentionally simple and explainable
    for a portfolio-scale control example.
    """
    if settling_band_m <= 0:
        raise ValueError("settling_band_m must be positive")
    if steady_state_window_s <= 0:
        raise ValueError("steady_state_window_s must be positive")
    if pump_power_kw < 0:
        raise ValueError("pump_power_kw must be non-negative")

    error = result.error_m
    abs_error = np.abs(error)
    setpoint_reference = max(float(np.mean(result.setpoint_m)), 1e-9)

    overshoot_m = max(float(np.max(result.level_m - result.setpoint_m)), 0.0)
    overshoot_percent = 100.0 * overshoot_m / setpoint_reference
    settling_time_s = _settling_time(result.time_s, abs_error, settling_band_m)

    dt_s = _median_dt(result.time_s)
    tail_samples = min(len(error), max(1, int(round(steady_state_window_s / dt_s))))
    tail_error = error[-tail_samples:]

    pump_energy_kwh = float(_integrate(result.pump_command, result.time_s) / 3600.0 * pump_power_kw)
    pumped_volume_m3 = float(_integrate(result.pump_flow_m3_s, result.time_s))

    return PerformanceMetrics(
        controller=result.controller_name,
        overshoot_m=overshoot_m,
        overshoot_percent=overshoot_percent,
        settling_time_s=settling_time_s,
        steady_state_error_m=float(np.mean(tail_error)),
        mean_absolute_error_m=float(np.mean(abs_error)),
        pump_energy_kwh=pump_energy_kwh,
        pumped_volume_m3=pumped_volume_m3,
        max_pump_command_percent=float(100.0 * np.max(result.pump_command)),
    )


def metrics_table(
    results: Sequence[SimulationResult],
    *,
    settling_band_m: float = 0.03,
    steady_state_window_s: float = 180.0,
    pump_power_kw: float = 1.5,
) -> pd.DataFrame:
    """Return a pandas table with one metric row per controller."""
    rows = [
        asdict(
            calculate_metrics(
                result,
                settling_band_m=settling_band_m,
                steady_state_window_s=steady_state_window_s,
                pump_power_kw=pump_power_kw,
            )
        )
        for result in results
    ]
    return pd.DataFrame(rows)


def _settling_time(time_s: np.ndarray, abs_error: np.ndarray, band_m: float) -> float:
    for index, error_m in enumerate(abs_error):
        if error_m <= band_m and bool(np.all(abs_error[index:] <= band_m)):
            return float(time_s[index])
    return float("nan")


def _median_dt(time_s: np.ndarray) -> float:
    if len(time_s) < 2:
        return 1.0
    return float(np.median(np.diff(time_s)))


def _integrate(y: np.ndarray, x: np.ndarray) -> float:
    trapezoid = getattr(np, "trapezoid", None)
    if trapezoid is not None:
        return float(trapezoid(y, x))
    return float(np.trapz(y, x))
