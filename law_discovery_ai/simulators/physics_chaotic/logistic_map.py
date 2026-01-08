import uuid
from ..world_export import export_world

def run_logistic_map(r=3.9, x0=0.5, timesteps=100, interventions=None):
    """
    Simulates the logistic map: x_{t+1} = r * x_t * (1 - x_t).

    Args:
        r (float): Control parameter.
        x0 (float): Initial value (0 < x0 < 1).
        timesteps (int): Number of steps to simulate.
        interventions (list): List of dictionaries defining interventions.
                              Example: [{"time": 10, "parameter": "x", "new_value": 0.8}]

    Returns:
        dict: Standardized world dictionary.
    """
    if interventions is None:
        interventions = []

    # Sort interventions by time
    sorted_interventions = sorted(interventions, key=lambda x: x["time"])
    intervention_idx = 0

    parameters = {
        "r": r,
        "x0": x0,
        "timesteps": timesteps
    }

    time_series = []

    # Initial state
    current_x = x0
    current_time = 0

    time_series.append({
        "time_step": current_time,
        "x": current_x
    })

    while current_time < timesteps:
        next_time = current_time + 1

        # Check for interventions at the current step (before update or after? instructions say "At the specified time_step")
        # For discrete maps, "at step T" usually means before calculating T+1, or replacing x_T.
        # "Replace the current x value with new_value" -> then continue.
        # Let's assume intervention at time T affects the state at time T, overriding the previous calculation or initial condition.
        # But here we are iterating. We have x_t. We compute x_{t+1}.
        # If intervention says "time": t, do we replace x_t before computing x_{t+1}?
        # Or do we replace x_t after it was computed?
        # Standard interpretation: "At time t, set parameter/variable to value".
        # If we have [x0, x1, ...], and intervention is at t=5. We set x5 = val.
        # Then x6 is computed from new x5.

        # My loop structure:
        # We are at current_time (say t). We have x_t stored in current_x.
        # We want to compute x_{t+1}.
        # Wait, if intervention is at t, we should have applied it before recording t?
        # Or is it an intervention *during* the transition?

        # Let's align with the prompt: "At the specified time_step: Replace the current x value with new_value; Continue deterministic iteration; Log the intervention verbatim".
        # This implies: At step T, we force x to be V.
        # Since we already recorded step 0 (x0), if intervention is at step 0, we should have updated it?
        # Usually interventions happen > 0.

        # Let's check interventions for the *next* step before we calculate it?
        # No, "At the specified time_step" usually means "When time is T".
        # If we just finished step T (current_time), and we are about to move to T+1.
        # Wait, x is the state.
        # Let's assume intervention at T means "After arriving at T, change state to V, then proceed to T+1".
        # But we already logged T.
        # If we change x_T, we should technically update the log for T or log it as a separate event?
        # The prompt says "Log the intervention verbatim" in the export, not necessarily in the time series.
        # But the physics must reflect it.

        # Implementation choice:
        # We compute x_{t+1} naturally.
        # THEN we check if there is an intervention for t+1.
        # If so, we overwrite x_{t+1}.
        # THEN we log (t+1, x_{t+1}).

        # What if intervention is for t=0? We already set it.
        # Let's handle t=0 special case or generally:
        # Ideally, we check intervention for `next_time` AFTER computing natural evolution, but BEFORE logging/using it for next step.

        # Calculate natural next state
        next_x = r * current_x * (1 - current_x)

        # Process interventions for next_time
        while intervention_idx < len(sorted_interventions):
            intv = sorted_interventions[intervention_idx]
            intv_time = intv["time"]

            if intv_time == next_time:
                if intv["parameter"] == "x":
                    next_x = intv["new_value"]
                intervention_idx += 1
            elif intv_time < next_time:
                # Should have been processed?
                intervention_idx += 1
            else:
                # intv_time > next_time
                break

        current_time = next_time
        current_x = next_x

        time_series.append({
            "time_step": current_time,
            "x": current_x
        })

    world_id = str(uuid.uuid4())

    return export_world(
        world_id=world_id,
        world_type="chaotic",
        parameters=parameters,
        state_variables=["x", "time_step"],
        time_series=time_series,
        interventions=interventions,
        noise_model=None,
        notes="Deterministic chaotic map; no stochasticity"
    )
