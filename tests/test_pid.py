"""Tests for the PID controller."""

from __future__ import annotations

import pytest

from water_level_control.pid import PIDController


def test_pid_output_increases_for_larger_positive_error() -> None:
    """A larger positive error should request more pump power."""
    controller = PIDController(kp=0.5, name="P")

    small_error_output = controller.update(error=0.2, dt_s=1.0)
    controller.reset()
    large_error_output = controller.update(error=0.8, dt_s=1.0)

    assert large_error_output > small_error_output


def test_integral_state_is_limited() -> None:
    """The accumulated I state must stay inside configured limits."""
    controller = PIDController(
        kp=0.0,
        ki=0.2,
        output_limits=(-10.0, 10.0),
        integral_limits=(-2.0, 2.0),
    )

    for _ in range(20):
        controller.update(error=1.0, dt_s=1.0)

    assert controller.integral_state == pytest.approx(2.0)
    assert controller.last_terms.integral == pytest.approx(0.4)


def test_integral_pauses_when_output_saturates() -> None:
    """Anti-windup prevents integration deeper into actuator saturation."""
    controller = PIDController(
        kp=10.0,
        ki=1.0,
        output_limits=(0.0, 1.0),
        integral_limits=(-100.0, 100.0),
    )

    output = controller.update(error=1.0, dt_s=1.0)

    assert output == pytest.approx(1.0)
    assert controller.integral_state == pytest.approx(0.0)


def test_pid_rejects_non_positive_time_step() -> None:
    """The discrete controller requires a positive sample time."""
    controller = PIDController(kp=1.0)

    with pytest.raises(ValueError, match="dt_s"):
        controller.update(error=0.1, dt_s=0.0)
