import numpy as np

def encode_observations(simulator_output):
    """
    Converts raw simulator output into a standardized numerical form.

    Args:
        simulator_output (dict): The dictionary returned by the simulator.

    Returns:
        dict: A dictionary containing:
            - "variables": List of variable names (columns).
            - "data_matrix": numpy.ndarray of the data.
    """
    variables = simulator_output["state_variables"]
    time_series = simulator_output["time_series"]

    data_rows = []
    for entry in time_series:
        row = [entry[var] for var in variables]
        data_rows.append(row)

    data_matrix = np.array(data_rows)

    return {
        "variables": variables,
        "data_matrix": data_matrix
    }
