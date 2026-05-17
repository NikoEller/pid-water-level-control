"""Tests for the tank model and simulation loop."""

from __future__ import annotations

import numpy as np
import pytest

from water_level_control.pid import PIDController
from water_level_control.simulation import SimulationConfig, run_simulation, step_disturbance
from water_level_control.tank_model import TankParameters, WaterTank


def test_tank_level_is_clipped_to_physical_bounds() -> None:
    """Extreme inflow and pump commands must not produce impossible levels."""
    tank = WaterTank(
        parameters=TankParameters(
            area_m2=10.0,
            max_height_m=2.0,
            outlet_coefficient_m25_s=0.0,
            pump_capacity_m3_s=1.0,
        ),
        level_m=1.0,
    )

    assert tank.step(dt_s=100.0, inflow_m3_s=1.0, pump_command=0.0) == pytest.approx(2.0)
    assert tank.step(dt_s=100.0, inflow_m3_s=0.0, pump_command=1.0) == pytest.approx(0.0)


def test_tank_derivative_responds_to_flows() -> None:
    """More inflow raises the level derivative, pump flow lowers it."""
    tank = WaterTank(
        parameters=TankParameters(
            area_m2=20.0,
            max_height_m=3.0,
            outlet_coefficient_m25_s=0.0,
            pump_capacity_m3_s=0.1,
        ),
        level_m=1.0,
    )

    filling = tank.derivative(inflow_m3_s=0.2, pump_command=0.0)
    pumping = tank.derivative(inflow_m3_s=0.0, pump_command=1.0)

    assert filling > 0.0
    assert pumping < 0.0


def test_simulation_produces_expected_arrays() -> None:
    """The simulation result should contain aligned arrays with valid values."""
    config = SimulationConfig(
        duration_s=20.0,
        dt_s=2.0,
        initial_level_m=1.0,
        setpoint_m=1.1,
        base_inflow_m3_s=0.02,
        tank=TankParameters(max_height_m=2.0),
    )
    controller = PIDController(kp=2.0, name="P")

    result = run_simulation(
        config,
        controller=controller,
        disturbance=step_disturbance(start_s=6.0, end_s=10.0, inflow_m3_s=0.03),
    )

    expected_length = 11
    assert len(result.time_s) == expected_length
    assert result.level_m.shape == result.time_s.shape
    assert result.pump_command.shape == result.time_s.shape
    assert result.inflow_m3_s.shape == result.time_s.shape
    assert np.all(result.level_m >= 0.0)
    assert np.all(result.level_m <= config.tank.max_height_m)
    assert np.all((0.0 <= result.pump_command) & (result.pump_command <= 1.0))
    assert np.max(result.rain_inflow_m3_s) == pytest.approx(0.03)
