import uuid
import numpy as np
from ..world_export import export_world

def run_stochastic_simulator(time_step=0.1, total_time=10.0, initial_position=0.0, initial_velocity=0.0, gravity=9.81, noise_std=0.1, seed=42, interventions=None):
    """
    Simulates a particle falling under gravity with Gaussian noise on acceleration.

    Args:
        time_step (float): Time difference between observations.
        total_time (float): Total duration of simulation.
        initial_position (float): Starting position (m).
        initial_velocity (float): Starting velocity (m/s).
        gravity (float): Gravitational acceleration (m/s^2).
        noise_std (float): Standard deviation of Gaussian noise added to acceleration.
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

    # State initialization
    current_time = 0.0
    position = initial_position
    velocity = initial_velocity
    current_gravity = gravity

    parameters = {
        "time_step": time_step,
        "total_time": total_time,
        "initial_position": initial_position,
        "initial_velocity": initial_velocity,
        "initial_gravity": gravity,
        "noise_std": noise_std,
        "seed": seed
    }

    time_series = []

    # Record initial state
    # Initial acceleration has noise? Usually observations have noise or dynamics.
    # "add Gaussian noise to acceleration" -> dynamics noise.
    # a_t = -g + noise
    current_acceleration = -current_gravity + np.random.normal(0, noise_std)

    time_series.append({
        "time": current_time,
        "position": position,
        "velocity": velocity,
        "acceleration": current_acceleration
    })

    while current_time < total_time:
        next_time = current_time + time_step

        # Process interventions
        while intervention_idx < len(sorted_interventions):
            intv = sorted_interventions[intervention_idx]
            intv_time = intv["time"]

            if intv_time <= current_time + 1e-9:
                if intv["parameter"] == "gravity":
                    current_gravity = intv["new_value"]
                intervention_idx += 1
            else:
                break

        # Calculate acceleration with noise
        noise = np.random.normal(0, noise_std)
        acceleration = -current_gravity + noise

        # Update physics (Euler)
        # v_new = v + a * dt
        # x_new = x + v * dt + 0.5 * a * dt^2
        position = position + velocity * time_step + 0.5 * acceleration * (time_step ** 2)
        velocity = velocity + acceleration * time_step

        current_time = next_time

        time_series.append({
            "time": float(f"{current_time:.4f}"),
            "position": position,
            "velocity": velocity,
            "acceleration": acceleration
        })

    world_id = str(uuid.uuid4())

    return export_world(
        world_id=world_id,
        world_type="stochastic",
        parameters=parameters,
        state_variables=["position", "velocity", "acceleration", "time"],
        time_series=time_series,
        interventions=interventions,
        noise_model=f"Gaussian(0, {noise_std}) on acceleration",
        notes="Stochastic free fall simulation with noisy acceleration"
    )
