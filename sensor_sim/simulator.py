from __future__ import annotations
import math
import random
from typing import Optional

from .models import EnergyModel, NodeConfig, SimResult
from .policies import BasePolicy


def ground_truth(t_s: int, cfg: NodeConfig) -> float:
    # A smooth periodic signal with mild drift-like variation
    w = (2 * math.pi) / max(1.0, cfg.signal_period_s)
    return cfg.signal_base + cfg.signal_amp * math.sin(w * t_s) + 0.25 * math.sin(w * 0.33 * t_s)


def simulate(policy: BasePolicy, cfg: NodeConfig, energy: EnergyModel) -> SimResult:
    """Run the simulation.

    Notes:
    - Discrete time simulation with step dt_s (default 1s).
    - When the node is asleep, no sensing/CPU/tx occurs.
    - Energy is accumulated per time step + per action.
    """
    random.seed(cfg.seed)
    policy.reset()

    t: list[float] = []
    truth: list[float] = []
    measured: list[Optional[float]] = []
    sent: list[bool] = []
    reconstructed: list[float] = []

    # Energy bookkeeping
    e_sleep = 0.0
    e_idle = 0.0
    e_sense = 0.0
    e_cpu = 0.0
    e_tx = 0.0

    last_measurement: Optional[float] = None
    last_tx_value: Optional[float] = None
    last_tx_s: Optional[int] = None

    samples_taken = 0
    packets_sent = 0

    # reconstruction: start at truth(0)
    recon_val = ground_truth(0, cfg)

    steps = int(cfg.duration_s / cfg.dt_s)
    for i in range(steps + 1):
        now_s = int(round(i * cfg.dt_s))
        t.append(now_s)

        gt = ground_truth(now_s, cfg)
        truth.append(gt)

        out = policy.step(now_s, last_measurement, last_tx_s)

        if out.awake:
            e_idle += energy.e_idle_awake(cfg.dt_s)
        else:
            e_sleep += energy.e_sleep(cfg.dt_s)

        mval: Optional[float] = None
        did_tx = False

        if out.awake and out.take_sample:
            # Sense + CPU
            noise = random.gauss(0.0, cfg.noise_std)
            mval = gt + noise
            last_measurement = mval

            e_sense += energy.e_sense()
            e_cpu += energy.e_cpu()
            samples_taken += 1

        if out.awake and out.transmit and (last_measurement is not None):
            # Transmit latest measurement
            e_tx += energy.e_tx(cfg.payload_bytes)
            packets_sent += 1
            last_tx_s = now_s
            last_tx_value = last_measurement
            recon_val = last_measurement
            did_tx = True

        measured.append(mval)
        sent.append(did_tx)
        reconstructed.append(recon_val)

    # Data quality: MAE between truth and reconstructed
    abs_err_sum = 0.0
    for gt, rv in zip(truth, reconstructed):
        abs_err_sum += abs(gt - rv)
    mae = abs_err_sum / max(1, len(truth))

    e_total = e_sleep + e_idle + e_sense + e_cpu + e_tx
    breakdown = {
        "sleep": e_sleep,
        "idle_awake": e_idle,
        "sensing": e_sense,
        "cpu": e_cpu,
        "tx": e_tx,
    }

    return SimResult(
        t=t,
        truth=truth,
        measured=measured,
        sent=sent,
        reconstructed=reconstructed,
        energy_total_mj=e_total,
        energy_breakdown_mj=breakdown,
        samples_taken=samples_taken,
        packets_sent=packets_sent,
        mae=mae,
    )
