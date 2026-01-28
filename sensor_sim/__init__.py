"""Energy-Aware Sensor Node Simulator.

A small, self-contained Python simulator that models:
- periodic sensing
- CPU processing
- wireless transmission (mocked)
- sleep/awake duty cycling
- different sampling/transmit policies
"""

__all__ = ["simulator", "models", "policies", "plotting"]
__version__ = "1.0.0"
