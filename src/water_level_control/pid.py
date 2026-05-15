"""PID controller with output limiting and integral anti-windup."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class PIDTerms:
    """Breakdown of the latest PID calculation."""

    proportional: float
    integral: float
    derivative: float
    raw_output: float
    output: float
    integral_state: float


@dataclass
class PIDController:
    """Discrete PID controller for a normalized pump command.

    The controller expects an error signal where positive values should increase
    the output. In this project the simulation passes ``level - setpoint`` so
    that high water levels increase the pump command.
    """

    kp: float
    ki: float = 0.0
    kd: float = 0.0
    name: str = "PID"
    output_limits: tuple[float, float] = (0.0, 1.0)
    integral_limits: tuple[float, float] = (-120.0, 120.0)
    bias: float = 0.0
    _integral_state: float = field(default=0.0, init=False, repr=False)
    _previous_error: float | None = field(default=None, init=False, repr=False)
    _last_terms: PIDTerms = field(
        default_factory=lambda: PIDTerms(0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
        init=False,
        repr=False,
    )

    def __post_init__(self) -> None:
        """Validate controller limits."""
        low, high = self.output_limits
        if high <= low:
            raise ValueError("output_limits must be ordered as (low, high)")
        integral_low, integral_high = self.integral_limits
        if integral_high < integral_low:
            raise ValueError("integral_limits must be ordered as (low, high)")

    @property
    def integral_state(self) -> float:
        """Return the unclamped accumulated error state."""
        return self._integral_state

    @property
    def last_terms(self) -> PIDTerms:
        """Return P, I and D contributions from the latest update."""
        return self._last_terms

    def reset(self) -> None:
        """Clear integral and derivative memory."""
        self._integral_state = 0.0
        self._previous_error = None
        self._last_terms = PIDTerms(0.0, 0.0, 0.0, self.bias, self._clip_output(self.bias), 0.0)

    def update(self, error: float, dt_s: float) -> float:
        """Return the next controller output.

        Anti-windup is implemented in two layers: the integral state is clamped
        to configured limits, and integration pauses when the actuator is
        saturated in the same direction as the current error.
        """
        if dt_s <= 0:
            raise ValueError("dt_s must be positive")

        derivative = 0.0 if self._previous_error is None else (error - self._previous_error) / dt_s
        candidate_integral = self._clip_integral(self._integral_state + error * dt_s)

        raw_with_candidate = self._raw_output(error, candidate_integral, derivative)
        if self._should_accept_integral(error, raw_with_candidate):
            self._integral_state = candidate_integral

        raw_output = self._raw_output(error, self._integral_state, derivative)
        output = self._clip_output(raw_output)
        self._previous_error = error
        self._last_terms = PIDTerms(
            proportional=self.kp * error,
            integral=self.ki * self._integral_state,
            derivative=self.kd * derivative,
            raw_output=raw_output,
            output=output,
            integral_state=self._integral_state,
        )
        return output

    def _raw_output(self, error: float, integral_state: float, derivative: float) -> float:
        return self.bias + self.kp * error + self.ki * integral_state + self.kd * derivative

    def _should_accept_integral(self, error: float, raw_output: float) -> bool:
        low, high = self.output_limits
        if low <= raw_output <= high:
            return True
        if raw_output > high:
            return error < 0.0
        return error > 0.0

    def _clip_output(self, value: float) -> float:
        low, high = self.output_limits
        return min(max(value, low), high)

    def _clip_integral(self, value: float) -> float:
        low, high = self.integral_limits
        return min(max(value, low), high)
