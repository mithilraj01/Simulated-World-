import uuid
import numpy as np
from ..world_export import export_world

def run_whole_ocean_simulator(
    timesteps=50,
    width=5,
    height=5,
    depth_layers=5,
    surface_temp_base=20.0,
    bottom_temp_base=4.0,
    diffusion_rate=0.1,
    horizontal_transport_rate=0.05,
    seed=42,
    interventions=None
):
    """
    Simulates a large-scale liquid system (Whole Ocean) with spatial extent and vertical structure.

    Args:
        timesteps (int): Number of steps.
        width (int): Grid width (x).
        height (int): Grid height (y).
        depth_layers (int): Number of vertical layers (z).
        surface_temp_base (float): Base surface temperature.
        bottom_temp_base (float): Base bottom temperature.
        diffusion_rate (float): Vertical diffusion coefficient.
        horizontal_transport_rate (float): Horizontal mixing rate.
        seed (int): Random seed.
        interventions (list): List of interventions.

    Returns:
        dict: Standardized world dictionary.
    """
    if interventions is None:
        interventions = []

    np.random.seed(seed)

    sorted_interventions = sorted(interventions, key=lambda x: x["time"])
    intervention_idx = 0

    # Regime Descriptor
    regime_descriptor = {
        "regime": "liquid_continuum_extended",
        "valid_scales": {
            "length": {"min": "meters", "max": "planetary"},
            "time": {"min": "seconds", "max": "years"},
            "energy": {"min": "thermal", "max": "mechanical"}
        },
        "state_representation": "grid_of_vertical_fields",
        "fidelity_limits": "No Navier–Stokes, no Coriolis, no real ocean circulation; dynamics are phenomenological and density-parameterized",
        "handoff_rules": {
            "to_regime": "statistical",
            "conditions": "Spatial aggregation or loss of vertical resolution"
        }
    }

    parameters = {
        "timesteps": timesteps,
        "width": width,
        "height": height,
        "depth_layers": depth_layers,
        "surface_temp_base": surface_temp_base,
        "bottom_temp_base": bottom_temp_base,
        "diffusion_rate": diffusion_rate,
        "horizontal_transport_rate": horizontal_transport_rate,
        "seed": seed,
        "regime_descriptor": regime_descriptor
    }

    # Initialization
    # 3D Fields: T[x, y, z], P[x, y, z], Rho[x, y, z]
    # x: 0..width-1, y: 0..height-1, z: 0..depth-1 (0=Surface)

    T = np.zeros((width, height, depth_layers))
    P = np.zeros((width, height, depth_layers))
    Rho = np.zeros((width, height, depth_layers))

    # Initialize fields
    for x in range(width):
        for y in range(height):
            # Spatial variance in surface temp (e.g. latitudinal gradient if we mapped y to lat)
            # Let's add random regional variance
            local_surf = surface_temp_base + np.random.normal(0, 2.0)
            local_bot = bottom_temp_base + np.random.normal(0, 0.5)

            col_temps = np.linspace(local_surf, local_bot, depth_layers)
            col_temps += np.random.normal(0, 0.1, depth_layers)
            T[x, y, :] = col_temps

            # Pressure: Hydrostatic + noise
            col_press = np.array([1.0 + 0.1 * i for i in range(depth_layers)])
            col_press += np.random.normal(0, 0.001, depth_layers)
            P[x, y, :] = col_press

    # Density Function (Phenomenological)
    def update_density(temp, press):
        # rho = 1000 * (1 - alpha(T-4) + beta(P-1))
        return 1000.0 * (1.0 - 0.0002 * (temp - 4.0) + 0.00005 * (press - 1.0))

    Rho = update_density(T, P)

    time_series = []
    current_time = 0

    def get_snapshot(t, t_field, p_field, r_field):
        # Full export might be huge. Prompt says "Export full 3D fields".
        # We export lists of lists of lists.
        return {
            "time_step": t,
            "temperature_field": t_field.tolist(),
            "pressure_field": p_field.tolist(),
            "density_field": r_field.tolist(),
            "mean_surface_temp": np.mean(t_field[:, :, 0]),
            "mean_deep_temp": np.mean(t_field[:, :, -1])
        }

    time_series.append(get_snapshot(current_time, T, P, Rho))

    current_diffusion = diffusion_rate
    current_transport = horizontal_transport_rate

    while current_time < timesteps:
        next_time = current_time + 1

        # Interventions
        while intervention_idx < len(sorted_interventions):
            intv = sorted_interventions[intervention_idx]
            intv_time = intv["time"]

            if intv_time <= next_time:
                param = intv["parameter"]
                val = intv["new_value"]

                if param == "regional_heating":
                    # Heat specific region (e.g., x < width/2)
                    # "Interventions must be logged verbatim ... affect only local regions initially"
                    # We define "regional" as x=0..1, y=0..1 for simplicity or provided coords?
                    # Minimal implementation: Heat center region
                    cx, cy = width // 2, height // 2
                    T[cx, cy, 0] += val
                elif param == "deep_heating_pulse":
                    # Heat random deep spot
                    rx = np.random.randint(0, width)
                    ry = np.random.randint(0, height)
                    T[rx, ry, -1] += val
                elif param == "horizontal_mixing":
                    current_transport = val

                intervention_idx += 1
            else:
                break

        # Dynamics

        # 1. Vertical Diffusion (per column)
        # T_new = T + D * d2T/dz2
        # Vectorized operation over z axis
        # T[x, y, z] neighbors z-1, z+1

        T_diff = np.zeros_like(T)
        # Inner layers
        T_diff[:, :, 1:-1] = (T[:, :, 0:-2] - 2*T[:, :, 1:-1] + T[:, :, 2:])
        # Boundaries (flux from inner)
        T_diff[:, :, 0] = (T[:, :, 1] - T[:, :, 0])
        T_diff[:, :, -1] = (T[:, :, -2] - T[:, :, -1])

        # Apply random variation in diffusion rate
        local_D = current_diffusion * (1.0 + np.random.normal(0, 0.05, T.shape))
        T += local_D * T_diff

        # 2. Horizontal Transport (Exchange with neighbors)
        # Simple 4-neighbor averaging/diffusion
        # T_new[x,y] += H * (Sum(Neighbors) - 4*T[x,y])
        T_horiz = np.zeros_like(T)

        # We can implement this with slicing or loop. Loop is explicit.
        for x in range(width):
            for y in range(height):
                neighbors = []
                if x > 0: neighbors.append(T[x-1, y, :])
                if x < width-1: neighbors.append(T[x+1, y, :])
                if y > 0: neighbors.append(T[x, y-1, :])
                if y < height-1: neighbors.append(T[x, y+1, :])

                if not neighbors: continue

                # Stack neighbors to average
                neigh_sum = np.sum(neighbors, axis=0)
                count = len(neighbors)

                # Flux = Rate * (AvgNeighbor - Self)
                # Or Rate * Sum(Neigh - Self)
                # Let's do Rate * (Mean(Neighbors) - Self)
                T_horiz[x, y, :] = (neigh_sum / count) - T[x, y, :]

        # Apply transport with random variation
        local_H = current_transport * (1.0 + np.random.normal(0, 0.05, T.shape))
        T += local_H * T_horiz

        # 3. Thermal Noise
        T += np.random.normal(0, 0.005, T.shape)

        # 4. Pressure Drift
        P += np.random.normal(0, 0.0001, P.shape)

        # 5. Density Update
        Rho = update_density(T, P)

        # 6. Slow Vertical Motion (Convection/Overturn)
        # Check stability per column
        for x in range(width):
            for y in range(height):
                for z in range(depth_layers - 1):
                    # Unstable if Heavy (High Rho) on top of Light (Low Rho)
                    # Index z is shallower than z+1
                    if Rho[x, y, z] > Rho[x, y, z+1]:
                        # Mix
                        avg_T = (T[x, y, z] + T[x, y, z+1]) / 2.0
                        T[x, y, z] = avg_T
                        T[x, y, z+1] = avg_T
                        # Re-update density immediately to prevent oscillation?
                        # Or just wait for next step.
                        # Let's update local density for next check
                        Rho[x, y, z] = update_density(avg_T, P[x, y, z])
                        Rho[x, y, z+1] = update_density(avg_T, P[x, y, z+1])

        current_time = next_time
        time_series.append(get_snapshot(current_time, T, P, Rho))

    world_id = str(uuid.uuid4())

    state_variables = ["time_step", "temperature_field", "pressure_field", "density_field", "mean_surface_temp", "mean_deep_temp"]

    return export_world(
        world_id=world_id,
        world_type="whole_ocean_liquid",
        parameters=parameters,
        state_variables=state_variables,
        time_series=time_series,
        interventions=interventions,
        noise_model="Thermal noise, transport rate perturbation",
        notes="Phenomenological whole-ocean model; density-parameterized."
    )
