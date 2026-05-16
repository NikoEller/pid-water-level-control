"""Run a complete water level control demo and save results."""

from __future__ import annotations

import sys
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
MPL_CACHE_DIR = PROJECT_ROOT / ".cache" / "matplotlib"
MPL_CACHE_DIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("XDG_CACHE_HOME", str(PROJECT_ROOT / ".cache"))
os.environ.setdefault("MPLCONFIGDIR", str(MPL_CACHE_DIR))

from water_level_control.metrics import metrics_table
from water_level_control.pid import PIDController
from water_level_control.plotting import save_all_plots
from water_level_control.simulation import SimulationConfig, SimulationResult, run_simulation, step_disturbance
from water_level_control.tank_model import TankParameters


def build_demo_config() -> SimulationConfig:
    """Return a realistic small-basin simulation setup."""
    return SimulationConfig(
        duration_s=2_400.0,
        dt_s=1.0,
        initial_level_m=1.20,
        setpoint_m=1.20,
        base_inflow_m3_s=0.018,
        fixed_pump_command=0.02,
        tank=TankParameters(
            area_m2=25.0,
            max_height_m=3.0,
            outlet_coefficient_m25_s=0.015,
            pump_capacity_m3_s=0.08,
        ),
    )


def run_demo(output_dir: Path | str = PROJECT_ROOT / "results") -> list[SimulationResult]:
    """Run open-loop, P, PI and PID simulations and save artifacts."""
    config = build_demo_config()
    rain_event = step_disturbance(start_s=300.0, end_s=900.0, inflow_m3_s=0.055)

    controllers = [
        None,
        PIDController(kp=6.0, ki=0.0, kd=0.0, name="P"),
        PIDController(kp=8.0, ki=0.002, kd=0.0, name="PI"),
        PIDController(kp=12.0, ki=0.0015, kd=80.0, name="PID"),
    ]
    results = [run_simulation(config, controller, disturbance=rain_event) for controller in controllers]

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    table = metrics_table(results).round(
        {
            "overshoot_m": 4,
            "overshoot_percent": 2,
            "settling_time_s": 1,
            "steady_state_error_m": 4,
            "mean_absolute_error_m": 4,
            "pump_energy_kwh": 4,
            "pumped_volume_m3": 3,
            "max_pump_command_percent": 2,
        }
    )
    table.to_csv(output_path / "metrics_summary.csv", index=False)
    save_all_plots(results, output_path)
    return results


def main() -> None:
    """Run the demo from the command line."""
    results = run_demo()
    table = metrics_table(results).round(4)
    print("Saved plots and metrics to results/")
    print(table.to_string(index=False))


if __name__ == "__main__":
    main()
