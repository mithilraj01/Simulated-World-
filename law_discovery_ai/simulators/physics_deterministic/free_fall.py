def run_simulator(time_step=0.1, total_time=10.0, initial_position=0.0, initial_velocity=0.0):
    """
    Simulates a particle falling under constant gravity.

    Args:
        time_step (float): Time difference between observations.
        total_time (float): Total duration of simulation.
        initial_position (float): Starting position (m).
        initial_velocity (float): Starting velocity (m/s).

    Returns:
        dict: A dictionary containing state variables, time series data, interventions, and the ground truth law.
    """
    g = 9.81
    acceleration = -g

    times = []
    t = 0.0
    while t <= total_time + 1e-9: # handle float precision
        times.append(t)
        t += time_step

    time_series = []
    for t in times:
        # Using exact kinematic equations to ensure the ground truth law holds perfectly
        position = initial_position + initial_velocity * t + 0.5 * acceleration * (t ** 2)
        velocity = initial_velocity + acceleration * t

        entry = {
            "time": t,
            "position": position,
            "velocity": velocity,
            "acceleration": acceleration
        }
        time_series.append(entry)

    return {
        "state_variables": ["position", "velocity", "acceleration", "time"],
        "time_series": time_series,
        "interventions": [],
        "ground_truth_law": "x = x0 + v0*t + 0.5*a*t^2"
    }
