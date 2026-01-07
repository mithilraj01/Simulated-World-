def export_world(world_id, world_type, parameters, state_variables, time_series, interventions, noise_model, notes=""):
    """
    Exports the world data in a standardized dictionary format.

    Args:
        world_id (str): Unique identifier for the simulation run.
        world_type (str): Type of world (deterministic | stochastic | chaotic | biological).
        parameters (dict): Configuration parameters used for the simulation.
        state_variables (list): List of state variable names.
        time_series (list): List of dictionaries, each representing a time step.
        interventions (list): List of applied interventions.
        noise_model (str or None): Description of the noise model, or None.
        notes (str): Purely descriptive notes.

    Returns:
        dict: Standardized world dictionary.
    """
    return {
        "world_id": world_id,
        "world_type": world_type,
        "parameters": parameters,
        "state_variables": state_variables,
        "time_series": time_series,
        "interventions": interventions,
        "noise_model": noise_model,
        "notes": notes
    }
