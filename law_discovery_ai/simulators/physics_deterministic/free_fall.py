import uuid
from ..world_export import export_world

def run_simulator(time_step=0.1, total_time=10.0, initial_position=0.0, initial_velocity=0.0, gravity=9.81, interventions=None):
    """
    Simulates a particle falling under constant gravity.

    Args:
        time_step (float): Time difference between observations.
        total_time (float): Total duration of simulation.
        initial_position (float): Starting position (m).
        initial_velocity (float): Starting velocity (m/s).
        gravity (float): Gravitational acceleration (m/s^2).
        interventions (list): List of dictionaries defining interventions.
                              Example: [{"time": 2.0, "parameter": "gravity", "new_value": 1.62}]

    Returns:
        dict: Standardized world dictionary.
    """
    if interventions is None:
        interventions = []

    # Sort interventions by time to apply them in order
    sorted_interventions = sorted(interventions, key=lambda x: x["time"])
    intervention_idx = 0

    # State initialization
    current_time = 0.0
    position = initial_position
    velocity = initial_velocity
    current_gravity = gravity

    # Parameters for record
    parameters = {
        "time_step": time_step,
        "total_time": total_time,
        "initial_position": initial_position,
        "initial_velocity": initial_velocity,
        "initial_gravity": gravity
    }

    time_series = []

    # Record initial state
    acceleration = -current_gravity
    time_series.append({
        "time": current_time,
        "position": position,
        "velocity": velocity,
        "acceleration": acceleration
    })

    while current_time < total_time:
        # Check for interventions that happen at or before the next step
        # Note: Interventions are applied instantaneously at the specified time.
        # Since we are stepping discretely, we apply any interventions that fall within (current_time, current_time + time_step]
        # or exactly at current_time if not yet applied (though strictly, logic below handles "at this step").
        # However, to be "mechanical", if intervention says time=2.0, we apply it when simulation reaches 2.0.

        # Simple Euler integration for simulation step (or kinematic update if parameter is constant)
        # But since parameters can change, we step forward.

        # We process interventions that should happen before the physics update of the next step

        # Using a small epsilon for float comparison
        next_time = current_time + time_step

        # Process interventions
        while intervention_idx < len(sorted_interventions):
            intv = sorted_interventions[intervention_idx]
            intv_time = intv["time"]

            # If intervention is strictly in the future relative to current step logic, break
            # We assume intervention applies for the interval starting at intv_time.
            # If intv_time is between current_time and next_time, we might need to split the step or just apply it?
            # Instructions: "Apply interventions mechanically."
            # Simplest implementation: Apply if intv_time <= current_time.
            # But usually interventions happen *at* a time.
            # Let's check if we just passed it or it matches current_time.

            if intv_time <= current_time + 1e-9:
                # Apply intervention
                if intv["parameter"] == "gravity":
                    current_gravity = intv["new_value"]
                # Mark as applied by moving index
                intervention_idx += 1
            else:
                break

        # Update physics
        # Using simple Euler for flexibility with changing parameters
        # v = v + a * dt
        # x = x + v * dt + 0.5 * a * dt^2 (Kinematic for this step)

        # Acceleration depends on current gravity
        acceleration = -current_gravity

        # Update position and velocity
        # Note: If gravity changed exactly at current_time, we use the new gravity for this step.
        position = position + velocity * time_step + 0.5 * acceleration * (time_step ** 2)
        velocity = velocity + acceleration * time_step

        current_time = next_time

        time_series.append({
            "time": float(f"{current_time:.4f}"), # rounding to avoid float drift in logs
            "position": position,
            "velocity": velocity,
            "acceleration": acceleration
        })

    world_id = str(uuid.uuid4())

    return export_world(
        world_id=world_id,
        world_type="deterministic",
        parameters=parameters,
        state_variables=["position", "velocity", "acceleration", "time"],
        time_series=time_series,
        interventions=interventions,
        noise_model=None,
        notes="Deterministic free fall simulation"
    )
