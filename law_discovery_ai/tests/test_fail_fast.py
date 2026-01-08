import pytest
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from simulators.physics_deterministic.free_fall import run_simulator
from simulators.physics_chaotic.logistic_map import run_logistic_map

def test_invalid_parameters():
    """Verify system fails/behaves predictably on invalid parameters."""
    # This assumes simulators might raise errors or python standard errors occur.
    # PRD: "Fail-fast validation tests... assert the system raises errors"

    # If the simulators don't validate, python might raise TypeError or similar.

    # Test invalid type for parameter
    with pytest.raises(Exception):
        # run_simulator expects floats. If we pass a string, math ops should fail.
        run_simulator(gravity="high")

def test_chaotic_invalid_params():
    # x0 must be 0 < x0 < 1 for logistic map to stay bounded?
    # Actually, if r > 4, it escapes [0,1].
    # But if input is string, it should fail.
    with pytest.raises(Exception):
        run_logistic_map(r="chaos")

def test_intervention_invalid_structure():
    # Intervention without 'time' key
    bad_intv = [{"parameter": "x", "new_value": 0.5}]

    with pytest.raises(Exception):
        # Accessing x["time"] in code will raise KeyError
        run_logistic_map(interventions=bad_intv)

def test_intervention_time_type():
    # Intervention time as string might fail if code expects number comparison
    bad_intv = [{"time": "now", "parameter": "x", "new_value": 0.5}]
    with pytest.raises(Exception):
        run_logistic_map(interventions=bad_intv)
