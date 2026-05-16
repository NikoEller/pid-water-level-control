"""Plotting helpers for the demo and documentation figures."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from water_level_control.simulation import SimulationResult

COLORS: Mapping[str, str] = {
    "Open loop": "#4b5563",
    "P": "#2563eb",
    "PI": "#f97316",
    "PID": "#16a34a",
}


def save_all_plots(results: Sequence[SimulationResult], output_dir: Path | str) -> dict[str, Path]:
    """Create all standard result plots and return their file paths."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    result_by_name = {result.controller_name: result for result in results}
    reference = result_by_name.get("PID", results[-1])

    paths = {
        "water_level": output_path / "water_level_over_time.png",
        "setpoint_tracking": output_path / "setpoint_vs_actual_pid.png",
        "pump_command": output_path / "pump_command_over_time.png",
        "inflow": output_path / "inflow_disturbance.png",
        "controller_comparison": output_path / "controller_comparison.png",
    }
    plot_water_level(results, paths["water_level"])
    plot_setpoint_tracking(reference, paths["setpoint_tracking"])
    plot_pump_command(results, paths["pump_command"])
    plot_inflow(reference, paths["inflow"])
    plot_controller_comparison([result for result in results if result.controller_name != "Open loop"], paths["controller_comparison"])
    return paths


def plot_water_level(results: Sequence[SimulationResult], output_path: Path | str) -> None:
    """Plot the water level of all simulation runs."""
    fig, ax = plt.subplots(figsize=(9, 4.8))
    for result in results:
        ax.plot(_minutes(result), result.level_m, label=result.controller_name, color=_color(result))
    ax.plot(_minutes(results[0]), results[0].setpoint_m, "--", color="#111827", label="Sollwert")
    _format_time_axis(ax, ylabel="Wasserstand h in m", title="Wasserstand ueber Zeit")
    _save(fig, output_path)


def plot_setpoint_tracking(result: SimulationResult, output_path: Path | str) -> None:
    """Plot setpoint and actual level for one selected controller."""
    fig, ax = plt.subplots(figsize=(9, 4.8))
    ax.plot(_minutes(result), result.setpoint_m, "--", color="#111827", label="Sollwert")
    ax.plot(_minutes(result), result.level_m, color=_color(result), label=f"Istwert {result.controller_name}")
    ax.fill_between(
        _minutes(result),
        result.setpoint_m - 0.03,
        result.setpoint_m + 0.03,
        color="#94a3b8",
        alpha=0.18,
        label="+/- 3 cm Band",
    )
    _format_time_axis(ax, ylabel="Wasserstand h in m", title="Sollwert vs. Istwert")
    _save(fig, output_path)


def plot_pump_command(results: Sequence[SimulationResult], output_path: Path | str) -> None:
    """Plot normalized pump command in percent."""
    fig, ax = plt.subplots(figsize=(9, 4.8))
    for result in results:
        ax.plot(_minutes(result), 100.0 * result.pump_command, label=result.controller_name, color=_color(result))
    ax.set_ylim(-3, 103)
    _format_time_axis(ax, ylabel="Pumpenleistung in %", title="Stellgroesse der Pumpe")
    _save(fig, output_path)


def plot_inflow(result: SimulationResult, output_path: Path | str) -> None:
    """Plot base inflow and rain disturbance."""
    fig, ax = plt.subplots(figsize=(9, 4.8))
    ax.plot(_minutes(result), result.inflow_m3_s, color="#0f766e", label="Gesamtzufluss")
    ax.plot(_minutes(result), result.rain_inflow_m3_s, color="#0ea5e9", label="Regenstoerung")
    ax.set_ylim(bottom=0)
    _format_time_axis(ax, ylabel="Zufluss in m^3/s", title="Zufluss und Stoergroesse")
    _save(fig, output_path)


def plot_controller_comparison(results: Sequence[SimulationResult], output_path: Path | str) -> None:
    """Compare P, PI and PID controller responses."""
    fig, ax = plt.subplots(figsize=(9, 4.8))
    for result in results:
        ax.plot(_minutes(result), result.level_m, label=result.controller_name, color=_color(result))
    ax.plot(_minutes(results[0]), results[0].setpoint_m, "--", color="#111827", label="Sollwert")
    _format_time_axis(ax, ylabel="Wasserstand h in m", title="Vergleich P / PI / PID")
    _save(fig, output_path)


def _format_time_axis(ax: plt.Axes, *, ylabel: str, title: str) -> None:
    ax.set_title(title)
    ax.set_xlabel("Zeit in min")
    ax.set_ylabel(ylabel)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best")


def _minutes(result: SimulationResult):
    return result.time_s / 60.0


def _color(result: SimulationResult) -> str:
    return COLORS.get(result.controller_name, "#7c3aed")


def _save(fig: plt.Figure, output_path: Path | str) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
