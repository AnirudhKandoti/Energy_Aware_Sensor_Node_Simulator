from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class EnergyModel:
    """Energy model using simple power * time accounting.

    Units:
    - power_* in milliwatts (mW)
    - durations in seconds (s)
    - energy returned in millijoules (mJ), since mW*s = mJ
    """
    power_sleep_mw: float = 0.5
    power_idle_awake_mw: float = 15.0
    power_cpu_mw: float = 35.0
    power_sense_mw: float = 25.0
    power_tx_mw: float = 120.0

    # Action durations (seconds)
    t_sense_s: float = 0.010
    t_cpu_s: float = 0.004

    # Radio parameters (mocked)
    bitrate_bps: float = 250_000.0  # e.g., 250 kbps
    tx_overhead_s: float = 0.002    # startup/headers/etc.

    def e_sleep(self, dt_s: float) -> float:
        return self.power_sleep_mw * dt_s

    def e_idle_awake(self, dt_s: float) -> float:
        return self.power_idle_awake_mw * dt_s

    def e_sense(self) -> float:
        return self.power_sense_mw * self.t_sense_s

    def e_cpu(self) -> float:
        return self.power_cpu_mw * self.t_cpu_s

    def e_tx(self, payload_bytes: int) -> float:
        bits = payload_bytes * 8
        t_tx = self.tx_overhead_s + (bits / self.bitrate_bps)
        return self.power_tx_mw * t_tx


@dataclass(frozen=True)
class NodeConfig:
    """Configuration for the sensor node."""
    duration_s: int = 600            # total simulation time
    dt_s: float = 1.0                # simulation time step

    payload_bytes: int = 24          # bytes sent per transmission
    seed: int = 42                   # random seed

    # Ground-truth signal parameters (synthetic)
    signal_base: float = 20.0
    signal_amp: float = 3.0
    signal_period_s: float = 120.0
    noise_std: float = 0.2           # measurement noise (sensor noise)

    # For adaptive policy
    change_threshold: float = 0.5
    max_silence_s: int = 30


@dataclass
class SimResult:
    """Simulation outputs."""
    t: list[float]
    truth: list[float]
    measured: list[Optional[float]]
    sent: list[bool]
    reconstructed: list[float]

    energy_total_mj: float
    energy_breakdown_mj: dict[str, float]
    samples_taken: int
    packets_sent: int

    mae: float
