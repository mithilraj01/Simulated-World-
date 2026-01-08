import pytest
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from simulators.physics_chaotic.logistic_map import run_logistic_map

def test_chaos_sensitivity():
    """Verify structural divergence due to initial conditions."""
    x0 = 0.5
    epsilon = 1e-6

    # Run two simulations with tiny difference
    out1 = run_logistic_map(r=3.9, x0=x0, timesteps=50)
    out2 = run_logistic_map(r=3.9, x0=x0 + epsilon, timesteps=50)

    ts1 = out1["time_series"]
    ts2 = out2["time_series"]

    # Check that they start close
    assert abs(ts1[0]["x"] - ts2[0]["x"]) == pytest.approx(epsilon)

    # Check that they diverge significantly by the end
    # We don't measure lyapunov, just structural inequality
    final_diff = abs(ts1[-1]["x"] - ts2[-1]["x"])

    # For r=3.9, it should diverge.
    # Just asserting they are not equal is strictly sufficient for "structural divergence"
    # asserting > epsilon ensures they didn't converge or stay parallel
    assert final_diff > epsilon * 10
    assert ts1 != ts2

def test_chaos_schema_identity():
    """Verify schema is identical despite divergence."""
    out1 = run_logistic_map(timesteps=5)
    out2 = run_logistic_map(timesteps=5, x0=0.6)

    keys1 = set(out1.keys())
    keys2 = set(out2.keys())
    assert keys1 == keys2

    # State variables list should be identical
    assert out1["state_variables"] == out2["state_variables"]
