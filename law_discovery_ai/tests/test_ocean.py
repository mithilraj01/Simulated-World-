import pytest
import sys
import os
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from simulators.ocean_column_vertical.ocean_simulator import run_ocean_simulator

def test_ocean_schema():
    """Verify ocean world schema compliance."""
    output = run_ocean_simulator(timesteps=5, depth_layers=5)

    assert output["world_type"] == "ocean_column_vertical"
    assert "regime_descriptor" in output["parameters"]
    rd = output["parameters"]["regime_descriptor"]
    assert rd["regime"] == "liquid_continuum"
    assert rd["state_representation"] == "vertical_fields"

    ts = output["time_series"]
    entry = ts[0]
    keys = {"time_step", "temperature_profile", "pressure_profile", "density_profile", "mean_temperature", "gradient_magnitude"}
    assert set(entry.keys()) == keys

    # Check profiles are lists of length 5
    assert len(entry["temperature_profile"]) == 5
    assert len(entry["pressure_profile"]) == 5
    assert len(entry["density_profile"]) == 5

def test_ocean_pressure_monotonic():
    """Verify pressure increases with depth."""
    output = run_ocean_simulator(timesteps=1, depth_layers=10)
    ts = output["time_series"]
    P = ts[0]["pressure_profile"]

    # Check strict monotonicity
    for i in range(len(P) - 1):
        assert P[i+1] > P[i]

def test_ocean_reproducibility():
    """Verify reproducibility with fixed seed."""
    out1 = run_ocean_simulator(seed=42)
    out2 = run_ocean_simulator(seed=42)

    ts1 = out1["time_series"]
    ts2 = out2["time_series"]

    assert ts1 == ts2

def test_ocean_divergence():
    """Verify divergence with different seeds (thermal noise)."""
    out1 = run_ocean_simulator(seed=42)
    out2 = run_ocean_simulator(seed=43)

    ts1 = out1["time_series"]
    ts2 = out2["time_series"]

    # Should be different due to noise
    assert ts1 != ts2

def test_ocean_intervention():
    """Verify intervention (surface heating)."""
    # Intervention: heat surface by 50 deg at t=2
    intv = [{"time": 2, "parameter": "surface_heating", "new_value": 50.0}]
    output = run_ocean_simulator(timesteps=5, depth_layers=5, interventions=intv, seed=42)

    ts = output["time_series"]

    # t=1: normal evolution
    # t=2: intervention applied. T[0] += 50.

    T1 = ts[1]["temperature_profile"][0]
    T2 = ts[2]["temperature_profile"][0]

    # Should be significantly hotter, accounting for diffusion/mixing/noise.
    # 50 deg jump is huge.
    assert T2 > T1 + 40.0 # Conservative check

def test_ocean_convection():
    """Verify instability leads to mixing."""
    # Create unstable condition: Cold (dense) on top of Hot (light)?
    # No, density decreases with Temp. Hot is light. Cold is dense.
    # Unstable: Cold (Heavy) on top of Hot (Light).
    # Init: Surface=20 (Light), Bottom=4 (Dense). This is stable.
    # Let's force instability via intervention or init params?
    # run_ocean_simulator args allow surface/bottom temp.
    # Set Surface=0 (Cold/Dense), Bottom=100 (Hot/Light).

    output = run_ocean_simulator(timesteps=5, depth_layers=2, surface_temp=0.0, bottom_temp=100.0, seed=42)

    ts = output["time_series"]
    T_init = ts[0]["temperature_profile"]
    # T[0] ~ 0, T[1] ~ 100.
    # Density: rho(0) > rho(100).
    # Unstable -> Convection should trigger.
    # Convection logic: swap/mix neighbors if rho[i] > rho[i+1].

    # Check t=1. Convection should have mixed them.
    T_next = ts[1]["temperature_profile"]

    # They should be closer together than diffusion alone would do?
    # Mixing sets both to average.
    # Avg ~ 50.
    # If diffusion only (rate 0.1):
    # Flux = 0.1 * (100 - 0) = 10.
    # T[0] -> 10. T[1] -> 90.
    # If convection: T[0] -> 50, T[1] -> 50.

    # assert T[0] > 20 indicates strong mixing
    assert T_next[0] > 20.0
