"""Basic sanity check to ensure the simulator runs without errors."""
from sensor_sim.models import EnergyModel, NodeConfig
from sensor_sim.policies import FixedSamplingPolicy, DutyCyclingPolicy, AdaptiveThresholdPolicy
from sensor_sim.simulator import simulate

def run():
    cfg = NodeConfig(duration_s=60, seed=1)
    energy = EnergyModel()
    for pol in [
        FixedSamplingPolicy(sample_every_s=5),
        DutyCyclingPolicy(wake_every_s=10, awake_window_s=2, sample_every_s=5),
        AdaptiveThresholdPolicy(base_every_s=2, threshold=0.5, max_silence_s=30),
    ]:
        r = simulate(pol, cfg, energy)
        assert r.energy_total_mj > 0
        assert len(r.t) == len(r.truth) == len(r.reconstructed)

if __name__ == "__main__":
    run()
    print("Self-test OK")
