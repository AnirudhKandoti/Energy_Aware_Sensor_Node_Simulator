# Energy-Aware Sensor Node Simulator (runnable entry point)
# Usage:
#   python main.py --policy fixed --duration 600 --out results
#   python main.py --policy duty --out results
#   python main.py --policy adaptive --out results
#
# On Windows PowerShell:
#   python .\main.py --policy adaptive --out results

from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict

from sensor_sim.models import EnergyModel, NodeConfig
from sensor_sim.policies import FixedSamplingPolicy, DutyCyclingPolicy, AdaptiveThresholdPolicy
from sensor_sim.simulator import simulate
from sensor_sim.plotting import save_plots


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Energy-Aware Sensor Node Simulator")
    p.add_argument("--policy", choices=["fixed", "duty", "adaptive"], default="adaptive",
                   help="Which strategy/policy to simulate.")
    p.add_argument("--duration", type=int, default=600, help="Simulation duration in seconds.")
    p.add_argument("--out", default="results", help="Output directory for reports and plots.")
    p.add_argument("--seed", type=int, default=42, help="Random seed.")
    p.add_argument("--config", default="", help="Optional JSON config file path (overrides flags).")
    return p.parse_args()


def load_cfg(args: argparse.Namespace) -> NodeConfig:
    cfg = NodeConfig(duration_s=args.duration, seed=args.seed)
    if args.config:
        with open(args.config, "r", encoding="utf-8") as f:
            data = json.load(f)
        # only accept known keys
        d = asdict(cfg)
        for k, v in data.items():
            if k in d:
                d[k] = v
        cfg = NodeConfig(**d)
    return cfg


def build_policy(args: argparse.Namespace, cfg: NodeConfig):
    if args.policy == "fixed":
        # sample+tx every 5s
        return FixedSamplingPolicy(sample_every_s=5)
    if args.policy == "duty":
        # wake every 10s, stay awake 2s, and sample every 5s
        return DutyCyclingPolicy(wake_every_s=10, awake_window_s=2, sample_every_s=5)
    # adaptive default
    return AdaptiveThresholdPolicy(
        base_every_s=2,
        threshold=cfg.change_threshold,
        max_silence_s=cfg.max_silence_s,
    )


def main() -> int:
    args = parse_args()
    cfg = load_cfg(args)
    energy = EnergyModel()
    policy = build_policy(args, cfg)

    os.makedirs(args.out, exist_ok=True)
    result = simulate(policy, cfg, energy)

    # Save a JSON report
    report = {
        "policy": policy.name,
        "config": asdict(cfg),
        "energy_model": asdict(energy),
        "summary": {
            "duration_s": cfg.duration_s,
            "samples_taken": result.samples_taken,
            "packets_sent": result.packets_sent,
            "mae": result.mae,
            "energy_total_mj": result.energy_total_mj,
            "energy_breakdown_mj": result.energy_breakdown_mj,
        }
    }
    report_path = os.path.join(args.out, "report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    # Save plots (optional; safe if matplotlib missing)
    plot_dir = os.path.join(args.out, "plots")
    plots = save_plots(result, plot_dir, title=policy.name)

    print("=== Energy-Aware Sensor Node Simulator ===")
    print(f"Policy: {policy.name}")
    print(f"Duration: {cfg.duration_s}s")
    print(f"Samples taken: {result.samples_taken}")
    print(f"Packets sent: {result.packets_sent}")
    print(f"Data quality (MAE): {result.mae:.3f} (lower is better)")
    print(f"Total energy: {result.energy_total_mj:.1f} mJ")
    print("Energy breakdown (mJ):")
    for k, v in result.energy_breakdown_mj.items():
        print(f"  - {k}: {v:.1f}")

    print(f"\nSaved report: {report_path}")
    if plots:
        print(f"Saved plots in: {plot_dir}")
    else:
        print("Plots skipped (matplotlib not available).")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
