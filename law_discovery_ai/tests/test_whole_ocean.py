import pytest
import sys
import os
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from simulators.whole_ocean_liquid.whole_ocean_simulator import run_whole_ocean_simulator

def test_whole_ocean_schema():
    """Verify whole ocean world schema compliance."""
    output = run_whole_ocean_simulator(timesteps=5, width=2, height=2, depth_layers=3)

    assert output["world_type"] == "whole_ocean_liquid"
    assert "regime_descriptor" in output["parameters"]
    rd = output["parameters"]["regime_descriptor"]
    assert rd["regime"] == "liquid_continuum_extended"
    assert rd["state_representation"] == "grid_of_vertical_fields"

    ts = output["time_series"]
    entry = ts[0]
    keys = {"time_step", "temperature_field", "pressure_field", "density_field", "mean_surface_temp", "mean_deep_temp"}
    assert set(entry.keys()) == keys

    # Check 3D structure
    # T field should be 2x2x3
    T = np.array(entry["temperature_field"])
    assert T.shape == (2, 2, 3)

def test_whole_ocean_spatial_heterogeneity():
    """Verify spatial heterogeneity exists."""
    output = run_whole_ocean_simulator(timesteps=1, width=5, height=5, depth_layers=5)
    T = np.array(output["time_series"][0]["temperature_field"])

    # Check variance across x, y at surface (z=0)
    surface_slice = T[:, :, 0]
    assert np.var(surface_slice) > 0.0

def test_whole_ocean_reproducibility():
    """Verify reproducibility with fixed seed."""
    out1 = run_whole_ocean_simulator(seed=42)
    out2 = run_whole_ocean_simulator(seed=42)

    # Convert lists to allow equality check
    # Or just check string representation or specific fields
    ts1 = out1["time_series"]
    ts2 = out2["time_series"]

    # Check field values match
    assert ts1[0]["temperature_field"] == ts2[0]["temperature_field"]

def test_whole_ocean_divergence():
    """Verify divergence with different seeds."""
    out1 = run_whole_ocean_simulator(seed=42)
    out2 = run_whole_ocean_simulator(seed=43)

    ts1 = out1["time_series"]
    ts2 = out2["time_series"]

    assert ts1[0]["temperature_field"] != ts2[0]["temperature_field"] # Init noise differs

def test_whole_ocean_intervention_locality():
    """Verify intervention affects local region."""
    # Intervention: regional_heating (adds to center)
    intv = [{"time": 2, "parameter": "regional_heating", "new_value": 50.0}]
    output = run_whole_ocean_simulator(timesteps=5, width=3, height=3, depth_layers=3, interventions=intv, seed=42)

    ts = output["time_series"]

    # t=1: Pre-intervention
    T1 = np.array(ts[1]["temperature_field"])

    # t=2: Post-intervention (applied during step 1->2)
    T2 = np.array(ts[2]["temperature_field"])

    # Center: (1, 1). z=0 (surface).
    # Should increase by ~50.
    # T2[1,1,0] should be >> T1[1,1,0]
    center_diff = T2[1,1,0] - T1[1,1,0]

    # Corner: (0, 0). Should NOT increase by 50 immediately (only diffusion/transport later).
    # Transport rate is small (0.05).
    corner_diff = T2[0,0,0] - T1[0,0,0]

    # Center diff should be much larger than corner diff
    assert center_diff > 40.0
    assert corner_diff < 10.0 # Allow for some noise/transport, but certainly not 50.

def test_whole_ocean_pressure_monotonic():
    """Verify pressure increases with depth."""
    output = run_whole_ocean_simulator(timesteps=1, width=2, height=2, depth_layers=5)
    P = np.array(output["time_series"][0]["pressure_field"])

    # Check for a single column
    col_P = P[0, 0, :]
    for i in range(len(col_P) - 1):
        assert col_P[i+1] > col_P[i]
