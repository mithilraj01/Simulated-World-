import pytest
import sys
import os
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from simulators.physics_deterministic.free_fall import run_simulator
from simulators.physics_stochastic.stochastic_free_fall import run_stochastic_simulator
from simulators.physics_chaotic.logistic_map import run_logistic_map

def test_deterministic_reproducibility():
    """Deterministic world must produce identical output for same input."""
    out1 = run_simulator(gravity=9.81, initial_velocity=0.0)
    out2 = run_simulator(gravity=9.81, initial_velocity=0.0)

    # Remove UUIDs for comparison
    id1 = out1.pop("world_id")
    id2 = out2.pop("world_id")

    # Structural and value equality
    assert out1 == out2
    assert id1 != id2 # UUIDs should differ

def test_chaotic_reproducibility():
    """Chaotic world must be deterministic."""
    out1 = run_logistic_map(r=3.9, x0=0.5)
    out2 = run_logistic_map(r=3.9, x0=0.5)

    id1 = out1.pop("world_id")
    id2 = out2.pop("world_id")

    assert out1 == out2
    assert id1 != id2

def test_stochastic_reproducibility_same_seed():
    """Stochastic world with same seed must match."""
    out1 = run_stochastic_simulator(seed=42)
    out2 = run_stochastic_simulator(seed=42)

    id1 = out1.pop("world_id")
    id2 = out2.pop("world_id")

    # We need to serialize to JSON string to ensure deep equality including floats?
    # Python dict comparison handles recursion.
    assert out1 == out2

def test_stochastic_divergence_diff_seed():
    """Stochastic world with different seeds must differ."""
    out1 = run_stochastic_simulator(seed=42)
    out2 = run_stochastic_simulator(seed=43)

    # Compare time series
    ts1 = out1["time_series"]
    ts2 = out2["time_series"]

    # They should differ in acceleration/velocity/position due to noise
    assert ts1 != ts2
