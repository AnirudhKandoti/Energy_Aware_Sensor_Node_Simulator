from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class PolicyOutput:
    awake: bool
    take_sample: bool
    transmit: bool


class BasePolicy:
    """Base class for sensor node policies."""
    name: str = "base"

    def reset(self) -> None:
        pass

    def step(self, t_s: int, last_measurement: Optional[float], last_tx_s: Optional[int]) -> PolicyOutput:
        raise NotImplementedError


class FixedSamplingPolicy(BasePolicy):
    """Always awake; sample and transmit every N seconds."""
    def __init__(self, sample_every_s: int = 5):
        self.sample_every_s = max(1, int(sample_every_s))
        self.name = f"fixed_{self.sample_every_s}s"

    def step(self, t_s: int, last_measurement: Optional[float], last_tx_s: Optional[int]) -> PolicyOutput:
        do = (t_s % self.sample_every_s == 0)
        return PolicyOutput(awake=True, take_sample=do, transmit=do)


class DutyCyclingPolicy(BasePolicy):
    """Duty-cycling: node sleeps most of the time, wakes in periodic windows.

    - wake_every_s: period between wake windows
    - awake_window_s: how long the node stays awake in that window
    - while awake, it samples+transmits every sample_every_s (aligned to global time)
    """
    def __init__(self, wake_every_s: int = 10, awake_window_s: int = 2, sample_every_s: int = 5):
        self.wake_every_s = max(1, int(wake_every_s))
        self.awake_window_s = max(1, int(awake_window_s))
        self.sample_every_s = max(1, int(sample_every_s))
        self.name = f"duty_w{self.wake_every_s}s_a{self.awake_window_s}s_s{self.sample_every_s}s"

    def step(self, t_s: int, last_measurement: Optional[float], last_tx_s: Optional[int]) -> PolicyOutput:
        phase = t_s % self.wake_every_s
        awake = (phase < self.awake_window_s)
        do = awake and (t_s % self.sample_every_s == 0)
        return PolicyOutput(awake=awake, take_sample=do, transmit=do)


class AdaptiveThresholdPolicy(BasePolicy):
    """Adaptive strategy:
    - Always awake (can be combined with duty cycling in real systems)
    - Sample every base_every_s
    - Transmit only if the measurement changed by >= threshold since last TX,
      OR if we've been silent for max_silence_s seconds (keep-alive).

    This reduces radio transmissions when the signal is stable.
    """
    def __init__(self, base_every_s: int = 2, threshold: float = 0.5, max_silence_s: int = 30):
        self.base_every_s = max(1, int(base_every_s))
        self.threshold = float(threshold)
        self.max_silence_s = max(1, int(max_silence_s))
        self.name = f"adaptive_b{self.base_every_s}s_th{self.threshold}_ms{self.max_silence_s}s"

        self._last_tx_value: Optional[float] = None

    def reset(self) -> None:
        self._last_tx_value = None

    def step(self, t_s: int, last_measurement: Optional[float], last_tx_s: Optional[int]) -> PolicyOutput:
        take_sample = (t_s % self.base_every_s == 0)
        transmit = False

        # Only decide about transmit if we are sampling now and have a measurement
        if take_sample and last_measurement is not None:
            if self._last_tx_value is None:
                transmit = True
            else:
                if abs(last_measurement - self._last_tx_value) >= self.threshold:
                    transmit = True

            if not transmit and last_tx_s is not None:
                if (t_s - last_tx_s) >= self.max_silence_s:
                    transmit = True

            if transmit:
                self._last_tx_value = last_measurement

        return PolicyOutput(awake=True, take_sample=take_sample, transmit=transmit)
