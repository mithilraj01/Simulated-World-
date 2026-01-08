import pytest
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from simulators.physics_deterministic.free_fall import run_simulator
from simulators.physics_chaotic.logistic_map import run_logistic_map

def test_deterministic_intervention():
    """Verify mechanical intervention in deterministic world."""
    # Run without intervention
    base = run_simulator(time_step=1.0, total_time=5.0, gravity=10.0)

    # Run with intervention: gravity -> 0 at t=2.0
    intervention = [{"time": 2.0, "parameter": "gravity", "new_value": 0.0}]
    intervened = run_simulator(time_step=1.0, total_time=5.0, gravity=10.0, interventions=intervention)

    # Check that output includes intervention
    assert intervened["interventions"] == intervention

    # Check dynamics
    # t=0, t=1: should match base (a=-10)
    # t=2: intervention applied.
    # Logic in simulator: intervention applies if intv_time <= current_time.
    # At t=2.0, gravity becomes 0.
    # So for step 2->3, acceleration should be 0.

    base_ts = base["time_series"]
    intv_ts = intervened["time_series"]

    # t=0, 1 should be identical (indices 0, 1)
    assert intv_ts[0] == base_ts[0]
    assert intv_ts[1] == base_ts[1]

    # t=2 (index 2) - state recorded before step 2->3?
    # Simulator logs state, then loops.
    # loop: update physics -> log.
    # Wait.
    # Initialization: t=0 log.
    # Loop t < total:
    #   process intv
    #   update physics (using current params)
    #   log new state

    # So at t=1.0 (index 1), we used gravity=10.
    # Next loop iteration: current_time=1.0. Next=2.0.
    # Process intv: if intv_time (2.0) <= current_time (1.0)? No.
    # Update physics: use g=10.
    # Log t=2.0. (index 2).
    # Next loop: current_time=2.0. Next=3.0.
    # Process intv: if intv_time (2.0) <= current_time (2.0)? Yes.
    # gravity -> 0.
    # Update physics: use g=0.
    # Log t=3.0. (index 3).

    # So t=3.0 should have acc=0.
    assert intv_ts[3]["acceleration"] == 0.0
    # Base case should still have -10
    assert base_ts[3]["acceleration"] == -10.0

def test_chaotic_intervention():
    """Verify mechanical intervention in chaotic world."""
    # x_{t+1} = r * x * (1-x)
    # t=0: x=0.2
    # Intervention at t=2: set x=0.5.

    # Logic in logistic map:
    # Init: t=0 log.
    # Loop t < steps:
    #   calc next_x (natural)
    #   check intv for next_time (t+1). If match, overwrite next_x.
    #   log t+1.

    intervention = [{"time": 2, "parameter": "x", "new_value": 0.5}]
    out = run_logistic_map(r=3.9, x0=0.2, timesteps=5, interventions=intervention)

    ts = out["time_series"]

    # t=2 should be exactly 0.5
    # ts is list. Index 2 is t=2.
    assert ts[2]["time_step"] == 2
    assert ts[2]["x"] == 0.5

    # t=3 should follow from 0.5
    # x_3 = 3.9 * 0.5 * 0.5 = 0.975
    assert abs(ts[3]["x"] - 0.975) < 1e-9
