import uuid
import numpy as np
from ..world_export import export_world

def run_ocean_simulator(
    timesteps=100,
    depth_layers=10,
    surface_temp=20.0,
    bottom_temp=4.0,
    diffusion_rate=0.1,
    seed=42,
    interventions=None
):
    """
    Simulates a vertical ocean column with continuous fields, gradients, and diffusion.

    Args:
        timesteps (int): Number of steps to simulate.
        depth_layers (int): Number of vertical layers.
        surface_temp (float): Initial temperature at the surface.
        bottom_temp (float): Initial temperature at the bottom.
        diffusion_rate (float): Thermal diffusion coefficient.
        seed (int): Random seed.
        interventions (list): List of interventions.

    Returns:
        dict: Standardized world dictionary.
    """
    if interventions is None:
        interventions = []

    np.random.seed(seed)

    # Sort interventions
    sorted_interventions = sorted(interventions, key=lambda x: x["time"])
    intervention_idx = 0

    # Regime Descriptor
    regime_descriptor = {
        "regime": "liquid_continuum",
        "valid_scales": {
            "length": {"min": "meters", "max": "kilometers"},
            "time": {"min": "seconds", "max": "years"},
            "energy": {"min": "thermal", "max": "mechanical"}
        },
        "state_representation": "vertical_fields",
        "fidelity_limits": "No Navier–Stokes, no turbulence modeling, no salinity chemistry; fields are coarse and phenomenological",
        "handoff_rules": {
            "to_regime": "statistical",
            "conditions": "Loss of spatial resolution or aggregation over depth"
        }
    }

    parameters = {
        "timesteps": timesteps,
        "depth_layers": depth_layers,
        "surface_temp": surface_temp,
        "bottom_temp": bottom_temp,
        "diffusion_rate": diffusion_rate,
        "seed": seed,
        "regime_descriptor": regime_descriptor
    }

    # Initialization
    # Layers: 0 (Surface) -> depth_layers-1 (Bottom)
    # Z coordinate: loosely 0 to depth_layers (meters or arbitrary units)

    # Temperature Profile: Linear gradient + small noise
    # T(z)
    temps = np.linspace(surface_temp, bottom_temp, depth_layers)
    # Add random perturbations (small)
    temps += np.random.normal(0, 0.05, depth_layers)

    # Pressure Profile: Hydrostatic P = rho * g * z
    # Phenomenological: P increases linearly with index + constant
    pressures = np.array([1.0 + 0.1 * i for i in range(depth_layers)]) # atm?

    # Density Profile: Phenomenological function of T and P
    # rho = rho0 * (1 - alpha * T + beta * P)
    # Simplification: rho decreases with T, increases with P
    def calculate_density(T, P):
        return 1000.0 * (1.0 - 0.0002 * (T - 4.0) + 0.00005 * (P - 1.0))

    densities = calculate_density(temps, pressures)

    state_variables = ["time_step", "temperature_profile", "pressure_profile", "density_profile", "mean_temperature", "gradient_magnitude"]

    time_series = []
    current_time = 0

    def get_snapshot(t, T_prof, P_prof, rho_prof):
        return {
            "time_step": t,
            "temperature_profile": T_prof.tolist(),
            "pressure_profile": P_prof.tolist(),
            "density_profile": rho_prof.tolist(),
            "mean_temperature": np.mean(T_prof),
            "gradient_magnitude": abs(T_prof[0] - T_prof[-1]) / depth_layers
        }

    time_series.append(get_snapshot(current_time, temps, pressures, densities))

    current_diffusion = diffusion_rate

    while current_time < timesteps:
        next_time = current_time + 1

        # Process Interventions
        while intervention_idx < len(sorted_interventions):
            intv = sorted_interventions[intervention_idx]
            intv_time = intv["time"]

            if intv_time <= next_time:
                param = intv["parameter"]
                val = intv["new_value"]

                if param == "surface_heating":
                    # Increase surface temp
                    temps[0] += val
                elif param == "deep_heating":
                    # Increase bottom temp
                    temps[-1] += val
                elif param == "mixing_pulse":
                    # Homogenize temperature partially
                    mean_T = np.mean(temps)
                    temps = temps * (1.0 - val) + mean_T * val
                elif param == "diffusion_rate":
                    current_diffusion = val

                intervention_idx += 1
            else:
                break

        # Dynamics

        # 1. Thermal Diffusion (1D Heat Equation)
        # T_new[i] = T[i] + k * (T[i-1] - 2T[i] + T[i+1])
        new_temps = temps.copy()

        # Apply stochastic fluctuation to diffusion rate per layer
        # "Noise & Instability: perturbations in diffusion rate"

        for i in range(1, depth_layers - 1):
            local_diff = current_diffusion * (1.0 + np.random.normal(0, 0.01))
            flux = local_diff * (temps[i-1] - 2*temps[i] + temps[i+1])
            new_temps[i] += flux

        # Boundary conditions
        # Surface: Coupled to air? Fixed or cooling?
        # Let's assume slight relaxation to ambient or just diffusion from below.
        # "surface heating" intervention implies it can change.
        # Let's keep boundaries relatively fixed or slowly drifting?
        # "temperature diffuses between neighboring layers"
        # Simplest: flux only from inner neighbor for boundaries.
        new_temps[0] += current_diffusion * (temps[1] - temps[0])
        new_temps[-1] += current_diffusion * (temps[-2] - temps[-1])

        # 2. Thermal Noise
        # "stochastic thermal noise"
        new_temps += np.random.normal(0, 0.001, depth_layers)

        temps = new_temps

        # 3. Pressure Update
        # "pressure updates mechanically based on depth ordering"
        # P is largely static in hydrostatic equilibrium unless mass changes.
        # Let's keep P profile static or add slight noise?
        # "accumulated numerical drift"
        # Let's add tiny drift to P to simulate changing column mass/atmosphere
        pressures += np.random.normal(0, 0.0001, depth_layers)

        # 4. Density Update
        # "density updates as a simple function of T and P"
        densities = calculate_density(temps, pressures)

        # 5. Vertical Motion (Optional)
        # "optional vertical motion based on density differences"
        # Convection: if lower layer is less dense than upper, swap or mix?
        # Unstable stratification.
        for i in range(depth_layers - 1):
            # Check instability: rho[i] (upper) > rho[i+1] (lower) -> stable
            # If rho[i] > rho[i+1], heavy on top of light -> unstable (if we assume z increases downwards)
            # Wait. z=0 is surface. z=N is bottom.
            # Pressure increases with index.
            # So index i is shallower than i+1.
            # Stable: rho[i] < rho[i+1]. Light on top of heavy.
            # Unstable: rho[i] > rho[i+1]. Heavy on top of light.

            if densities[i] > densities[i+1]:
                # Convective mixing / overturn
                # Swap or average? Real fluids mix.
                avg_T = (temps[i] + temps[i+1]) / 2.0
                temps[i] = avg_T
                temps[i+1] = avg_T
                # Re-calc density
                densities = calculate_density(temps, pressures)

        current_time = next_time
        time_series.append(get_snapshot(current_time, temps, pressures, densities))

    world_id = str(uuid.uuid4())

    return export_world(
        world_id=world_id,
        world_type="ocean_column_vertical",
        parameters=parameters,
        state_variables=state_variables,
        time_series=time_series,
        interventions=interventions,
        noise_model="Thermal noise, diffusion rate perturbation",
        notes="Phenomenological liquid column; no Navier-Stokes."
    )
