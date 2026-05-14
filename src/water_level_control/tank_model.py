"""Discrete water tank model used by the control simulations."""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt


@dataclass(frozen=True)
class TankParameters:
    """Physical parameters of a small retention basin or pump sump.

    Parameters
    ----------
    area_m2:
        Effective horizontal water surface area.
    max_height_m:
        Maximum physically meaningful water level used for clipping.
    outlet_coefficient_m25_s:
        Coefficient of the gravity outlet model ``q = c * sqrt(h)``.
        The compact unit name reflects that the factor maps sqrt(m) to m^3/s.
    pump_capacity_m3_s:
        Maximum pump outflow at a command of 1.0.
    """

    area_m2: float = 25.0
    max_height_m: float = 3.0
    outlet_coefficient_m25_s: float = 0.015
    pump_capacity_m3_s: float = 0.08

    def __post_init__(self) -> None:
        """Validate that the model can be simulated safely."""
        if self.area_m2 <= 0:
            raise ValueError("area_m2 must be positive")
        if self.max_height_m <= 0:
            raise ValueError("max_height_m must be positive")
        if self.outlet_coefficient_m25_s < 0:
            raise ValueError("outlet_coefficient_m25_s must be non-negative")
        if self.pump_capacity_m3_s < 0:
            raise ValueError("pump_capacity_m3_s must be non-negative")


@dataclass
class WaterTank:
    """Single-state tank model with Euler integration."""

    parameters: TankParameters
    level_m: float

    def __post_init__(self) -> None:
        """Clamp the initial water level to the physical tank range."""
        self.level_m = self._clip_level(self.level_m)

    def natural_outflow(self, level_m: float | None = None) -> float:
        """Return the gravity-driven outlet flow in m^3/s."""
        level = self.level_m if level_m is None else level_m
        return self.parameters.outlet_coefficient_m25_s * sqrt(max(level, 0.0))

    def pump_flow(self, pump_command: float) -> float:
        """Return the pump outflow in m^3/s for a normalized command."""
        command = min(max(pump_command, 0.0), 1.0)
        return command * self.parameters.pump_capacity_m3_s

    def derivative(self, inflow_m3_s: float, pump_command: float) -> float:
        """Return ``dh/dt`` for the current tank state.

        Positive values increase the water level, negative values lower it.
        """
        total_outflow = self.natural_outflow() + self.pump_flow(pump_command)
        return (inflow_m3_s - total_outflow) / self.parameters.area_m2

    def step(self, dt_s: float, inflow_m3_s: float, pump_command: float) -> float:
        """Advance the tank state by one explicit Euler step.

        The resulting level is clipped to ``[0, max_height_m]``. This keeps the
        discrete model physically meaningful even under extreme disturbances.
        """
        if dt_s <= 0:
            raise ValueError("dt_s must be positive")
        next_level = self.level_m + dt_s * self.derivative(inflow_m3_s, pump_command)
        self.level_m = self._clip_level(next_level)
        return self.level_m

    def _clip_level(self, level_m: float) -> float:
        return min(max(level_m, 0.0), self.parameters.max_height_m)
