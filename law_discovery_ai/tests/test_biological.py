import pytest
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from simulators.biological_agents_minimal.agent_simulator import run_biological_simulator

def test_biological_schema():
    """Verify biological world schema compliance."""
    output = run_biological_simulator(timesteps=5, initial_population=5)

    # Check standard keys
    assert "world_id" in output
    assert output["world_type"] == "biological_agents_minimal"
    assert "parameters" in output

    # Check regime descriptor
    params = output["parameters"]
    assert "regime_descriptor" in params
    rd = params["regime_descriptor"]
    assert rd["regime"] == "biological"
    assert "valid_scales" in rd

    # Check time series structure
    ts = output["time_series"]
    assert isinstance(ts, list)
    assert len(ts) == 6 # t=0 to t=5

    entry = ts[0]
    expected_keys = {"time_step", "temperature", "population_count", "average_energy", "resource_level", "agents"}
    assert set(entry.keys()) == expected_keys

    # Check agents list
    agents = entry["agents"]
    assert isinstance(agents, list)
    if len(agents) > 0:
        a = agents[0]
        assert {"id", "x", "energy", "age", "alive"}.issubset(set(a.keys()))

def test_biological_reproducibility():
    """Verify reproducibility with fixed seed."""
    out1 = run_biological_simulator(seed=42)
    out2 = run_biological_simulator(seed=42)

    # Exclude IDs and ensure structural equality
    out1_s = json_safe(out1)
    out2_s = json_safe(out2)

    assert out1_s == out2_s

def test_biological_divergence():
    """Verify divergence with different seeds."""
    out1 = run_biological_simulator(seed=42)
    out2 = run_biological_simulator(seed=43)

    # Populations should likely diverge in positions/counts
    ts1 = out1["time_series"]
    ts2 = out2["time_series"]

    assert ts1 != ts2

def test_biological_intervention():
    """Verify intervention works (e.g. temperature shift)."""
    # Intervention: set temperature to 100 at t=2 (should increase metabolic cost)
    intv = [{"time": 2, "parameter": "temperature", "new_value": 100.0}]

    out = run_biological_simulator(timesteps=5, initial_population=10, seed=42, interventions=intv)
    ts = out["time_series"]

    # t=0, 1: Temp = 1.0
    assert ts[1]["temperature"] == 1.0

    # t=2: Temp should be 100.0 (intervention applied before log/dynamics for step 2)
    # My logic:
    # Loop starts current_time=0. Log t=0.
    # While current < steps:
    #   next = current + 1
    #   process intv for next? "if intv_time <= next_time".
    #   If intv t=2. next=1. 2<=1 False.
    #   Dynamics. Log t=1.
    #   current=1.
    #   next=2.
    #   Process intv t=2. 2<=2 True. Apply. Temp=100.
    #   Dynamics (using Temp=100). Cost high.
    #   Log t=2.

    assert ts[2]["temperature"] == 100.0

    # High temp -> high metabolic cost -> energy drop
    # cost = 0.01 * (1 + abs(100-1)) = 0.01 * 100 = 1.0 energy per step.
    # Base cost at temp=1 is 0.01.
    # So avg energy should drop significantly at t=2 compared to no intervention.

    out_base = run_biological_simulator(timesteps=5, initial_population=10, seed=42)
    ts_base = out_base["time_series"]

    # Compare avg energy at t=2
    # At t=2, intv world had high cost during step 1->2.
    # Wait, my logic:
    #   current=1. next=2. Apply intv (Temp=100). Dynamics. Log t=2.
    # Yes, dynamics used Temp=100.

    assert ts[2]["average_energy"] < ts_base[2]["average_energy"]

# Helper to remove world_id for comparison
def json_safe(d):
    d = d.copy()
    del d["world_id"]
    return d
