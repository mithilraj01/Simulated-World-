import sympy

def select_best_law(surviving_hypotheses):
    """
    Selects the hypothesis with minimal Description Length.

    DL = number_of_symbols_in_expression + data_error

    Args:
        surviving_hypotheses (list): List of dicts from falsifier.

    Returns:
        dict: Result info.
    """
    if not surviving_hypotheses:
        return {
            "result": "IMPOSSIBLE",
            "expression": None,
            "description_length": float('inf')
        }

    best_hyp = None
    min_dl = float('inf')

    for item in surviving_hypotheses:
        expr = item["expression"]
        mse = item["mse"]

        # Count symbols (complexity)
        # sympy.count_ops returns the number of operations.
        # We assume this is a good proxy for "number of symbols".
        # visual=False ensures we count the tree structure.
        complexity = sympy.count_ops(expr, visual=False)

        # DL = complexity + data_error
        dl = complexity + mse

        if dl < min_dl:
            min_dl = dl
            best_hyp = item

    return {
        "result": "LAW",
        "expression": str(best_hyp["expression"]),
        "description_length": min_dl
    }
