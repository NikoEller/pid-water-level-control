"""Simulation loop for water level control experiments."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

import numpy as np
from numpy.typing import NDArray

from water_level_control.tank_model import TankParameters, WaterTank

FloatArray = NDArray[np.float64]
Signal = float | Callable[[float], float]


class FeedbackController(Protocol):
    """Protocol implemented by controllers used in the simulation loop."""

    name: str

    def reset(self) -> None:
        """Reset internal controller state before a simulation run."""

    def update(self, error: float, dt_s: float) -> float:
        """Calculate a normalized pump command from the current control error."""


@dataclass(frozen=True)
class SimulationConfig:
    """Configuration for one discrete simulation run."""

    duration_s: float = 1_800.0
    dt_s: float = 1.0
    initial_level_m: float = 1.0
    setpoint_m: Signal = 1.2
    base_inflow_m3_s: Signal = 0.018
    fixed_pump_command: float = 0.0
    tank: TankParameters = TankParameters()

    def __post_init__(self) -> None:
        """Validate numerical settings."""
        if self.duration_s <= 0:
            raise ValueError("duration_s must be positive")
        if self.dt_s <= 0:
            raise ValueError("dt_s must be positive")
        if not 0.0 <= self.fixed_pump_command <= 1.0:
            raise ValueError("fixed_pump_command must be in [0, 1]")


@dataclass(frozen=True)
class SimulationResult:
    """Time-series result of one simulation run."""

    controller_name: str
    time_s: FloatArray
    level_m: FloatArray
    setpoint_m: FloatArray
    pump_command: FloatArray
    inflow_m3_s: FloatArray
    rain_inflow_m3_s: FloatArray
    natural_outflow_m3_s: FloatArray
    pump_flow_m3_s: FloatArray

    @property
    def error_m(self) -> FloatArray:
        """Return water level error; positive means level above setpoint."""
        return self.level_m - self.setpoint_m


def run_simulation(
    config: SimulationConfig,
    controller: FeedbackController | None = None,
    disturbance: Callable[[float], float] | None = None,
) -> SimulationResult:
    """Run a closed-loop or open-loop water level simulation.

    The control error is defined as ``level - setpoint``. A positive error
    therefore means that the basin is too full and the pump command should rise.
    """
    time_s = np.arange(0.0, config.duration_s + config.dt_s, config.dt_s, dtype=float)
    n_steps = len(time_s)

    level_m = np.zeros(n_steps, dtype=float)
    setpoint_m = np.zeros(n_steps, dtype=float)
    pump_command = np.zeros(n_steps, dtype=float)
    inflow_m3_s = np.zeros(n_steps, dtype=float)
    rain_inflow_m3_s = np.zeros(n_steps, dtype=float)
    natural_outflow_m3_s = np.zeros(n_steps, dtype=float)
    pump_flow_m3_s = np.zeros(n_steps, dtype=float)

    tank = WaterTank(config.tank, config.initial_level_m)
    if controller is not None:
        controller.reset()

    for index, t_s in enumerate(time_s):
        current_setpoint = _signal_value(config.setpoint_m, t_s)
        current_base_inflow = _signal_value(config.base_inflow_m3_s, t_s)
        current_rain = 0.0 if disturbance is None else disturbance(t_s)
        current_inflow = max(current_base_inflow + current_rain, 0.0)

        if controller is None:
            command = config.fixed_pump_command
            controller_name = "Open loop"
        else:
            command = controller.update(tank.level_m - current_setpoint, config.dt_s)
            controller_name = controller.name

        command = float(np.clip(command, 0.0, 1.0))

        level_m[index] = tank.level_m
        setpoint_m[index] = current_setpoint
        pump_command[index] = command
        inflow_m3_s[index] = current_inflow
        rain_inflow_m3_s[index] = current_rain
        natural_outflow_m3_s[index] = tank.natural_outflow()
        pump_flow_m3_s[index] = tank.pump_flow(command)

        if index < n_steps - 1:
            tank.step(config.dt_s, current_inflow, command)

    return SimulationResult(
        controller_name=controller_name,
        time_s=time_s,
        level_m=level_m,
        setpoint_m=setpoint_m,
        pump_command=pump_command,
        inflow_m3_s=inflow_m3_s,
        rain_inflow_m3_s=rain_inflow_m3_s,
        natural_outflow_m3_s=natural_outflow_m3_s,
        pump_flow_m3_s=pump_flow_m3_s,
    )


def step_disturbance(
    start_s: float = 300.0,
    end_s: float = 900.0,
    inflow_m3_s: float = 0.055,
) -> Callable[[float], float]:
    """Create a rectangular rain inflow disturbance."""
    if end_s <= start_s:
        raise ValueError("end_s must be larger than start_s")
    if inflow_m3_s < 0:
        raise ValueError("inflow_m3_s must be non-negative")

    def rain(t_s: float) -> float:
        return inflow_m3_s if start_s <= t_s <= end_s else 0.0

    return rain


def _signal_value(signal: Signal, t_s: float) -> float:
    return float(signal(t_s) if callable(signal) else signal)
