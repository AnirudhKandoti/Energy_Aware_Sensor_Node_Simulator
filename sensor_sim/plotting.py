from __future__ import annotations
from typing import Optional
import os

from .models import SimResult


def _try_import_matplotlib():
    try:
        import matplotlib.pyplot as plt  # type: ignore
        return plt
    except Exception:
        return None


def save_plots(result: SimResult, out_dir: str, title: str) -> list[str]:
    """Save plots to out_dir.

    This function is safe even if matplotlib is not installed:
    it will simply return an empty list.
    """
    plt = _try_import_matplotlib()
    if plt is None:
        return []

    os.makedirs(out_dir, exist_ok=True)
    paths: list[str] = []

    # Plot 1: truth vs reconstructed
    plt.figure()
    plt.plot(result.t, result.truth, label="Ground truth")
    plt.plot(result.t, result.reconstructed, label="Reconstructed (what receiver sees)")
    plt.xlabel("Time (s)")
    plt.ylabel("Signal value")
    plt.title(f"{title} — Signal")
    plt.legend()
    p1 = os.path.join(out_dir, "signal.png")
    plt.tight_layout()
    plt.savefig(p1, dpi=160)
    plt.close()
    paths.append(p1)

    # Plot 2: cumulative energy
    # Reconstruct cumulative energy using breakdown proportions per step is complex;
    # instead show energy breakdown as bar chart + total scalar.
    plt.figure()
    labels = list(result.energy_breakdown_mj.keys())
    values = [result.energy_breakdown_mj[k] for k in labels]
    plt.bar(labels, values)
    plt.ylabel("Energy (mJ)")
    plt.title(f"{title} — Energy breakdown (Total: {result.energy_total_mj:.1f} mJ)")
    p2 = os.path.join(out_dir, "energy_breakdown.png")
    plt.tight_layout()
    plt.savefig(p2, dpi=160)
    plt.close()
    paths.append(p2)

    return paths
