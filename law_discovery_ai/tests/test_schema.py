import pytest
import sys
import os

# Ensure we can import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from simulators.physics_deterministic.free_fall import run_simulator
from simulators.physics_stochastic.stochastic_free_fall import run_stochastic_simulator
from simulators.physics_chaotic.logistic_map import run_logistic_map

REQUIRED_KEYS = {
    "world_id",
    "world_type",
    "parameters",
    "state_variables",
    "time_series",
    "interventions",
    "noise_model",
    "notes"
}

FORBIDDEN_KEYS = {
    "law",
    "equation",
    "explanation",
    "correct",
    "accuracy",
    "proof",
    "model",
    "prediction"
}

def check_schema(output):
    keys = set(output.keys())
    assert keys == REQUIRED_KEYS, f"Missing or extra keys: {keys ^ REQUIRED_KEYS}"

    # Check forbidden keys recursively
    def check_forbidden(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                assert k.lower() not in FORBIDDEN_KEYS, f"Forbidden key found: {k}"
                check_forbidden(v)
        elif isinstance(obj, list):
            for item in obj:
                check_forbidden(item)

    check_forbidden(output)

    # Check time_series structure
    assert isinstance(output["time_series"], list)
    state_vars = set(output["state_variables"])

    # For chaotic maps, time variable is "time_step"
    # For physics, it is "time"
    # The prompt says "time index".
    # Let's check what variables are in the list.

    for entry in output["time_series"]:
        assert isinstance(entry, dict)
        entry_keys = set(entry.keys())
        # The entry keys should match state_variables exactly
        # But wait, is time included in state_variables?
        # In free_fall.py: state_variables=["position", "velocity", "acceleration", "time"]
        # In logistic_map.py: state_variables=["x", "time_step"]
        assert entry_keys == state_vars, f"Time series entry keys {entry_keys} mismatch state variables {state_vars}"

def test_deterministic_schema():
    output = run_simulator(time_step=1.0, total_time=2.0)
    check_schema(output)

def test_stochastic_schema():
    output = run_stochastic_simulator(time_step=1.0, total_time=2.0)
    check_schema(output)

def test_chaotic_schema():
    output = run_logistic_map(timesteps=10)
    check_schema(output)
