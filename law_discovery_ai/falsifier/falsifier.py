import numpy as np
import sympy
from scipy.linalg import lstsq

def falsify_hypotheses(encoded_data, hypotheses, tolerance=1e-5):
    """
    Evaluates hypotheses against data and destroys incorrect ones.

    Args:
        encoded_data (dict): Output from encoder.
        hypotheses (list): List of sympy.Eq objects.
        tolerance (float): MSE threshold.

    Returns:
        list: Surviving hypotheses info (dict with expression, mse, parameters).
    """
    variables = encoded_data["variables"]
    data_matrix = encoded_data["data_matrix"]

    # Create a mapping from symbol name to data column
    # Ensure keys are strings
    var_map = {str(name): data_matrix[:, i] for i, name in enumerate(variables)}

    surviving_hypotheses = []

    for eq in hypotheses:
        lhs = eq.lhs
        rhs = eq.rhs

        # 1. Identify Target (LHS)
        if str(lhs) not in var_map:
            # If LHS is not a variable, we can't test it easily as "y = f(x)"
            # But the prompt implies we are checking laws.
            # Assuming LHS is a variable column.
            print(f"Skipping hypothesis {eq}: LHS {lhs} not found in variables.")
            continue

        y = var_map[str(lhs)]

        # 2. Identify Parameters (C0, C1, ...)
        # We look for symbols that are NOT in variables and start with C
        free_symbols = rhs.free_symbols
        # Variables in RHS must be in our data or be parameters

        params = []
        rhs_vars = []

        for sym in free_symbols:
            s_name = str(sym)
            if s_name in var_map:
                rhs_vars.append(sym)
            elif s_name.startswith('C') and s_name[1:].isdigit():
                params.append(sym)
            else:
                # Unknown symbol that is neither variable nor parameter?
                # Treat as parameter if not known?
                # The generator only produces C0, C1, C2.
                pass

        # Sort params to keep order deterministic
        params = sorted(params, key=lambda x: str(x))

        if not params:
            # Evaluate directly
            # lambdify
            try:
                # Use standard numpy
                f = sympy.lambdify(list(free_symbols), rhs, modules="numpy")

                # Prepare args
                args = [var_map[str(v)] for v in free_symbols]

                if not args:
                    # Constant RHS
                    val = float(rhs)
                    y_pred = np.full_like(y, val)
                else:
                    y_pred = f(*args)

                mse = np.mean((y - y_pred)**2)
                fitted_expr = eq

            except Exception as e:
                print(f"Error evaluating hypothesis {eq}: {e}")
                continue

        else:
            # Linear Regression
            # We assume the model is linear in parameters: y = sum(c_i * term_i)
            # Construct Design Matrix X
            X_cols = []
            valid_params = []

            for p in params:
                # Get the term associated with p
                # diff(rhs, p) returns the coefficient of p
                term = sympy.diff(rhs, p)

                # Check if term depends on other params (non-linear parameter dependence)
                # Our generator only produces linear combinations of params, so diff should remove the param.
                # e.g. diff(C0 + C1*t, C1) -> t

                # Evaluate term
                term_syms = list(term.free_symbols)

                # Check if we can evaluate
                try:
                    f_term = sympy.lambdify(term_syms, term, modules="numpy")
                    t_args = []
                    for s in term_syms:
                        if str(s) in var_map:
                            t_args.append(var_map[str(s)])
                        else:
                            # If term depends on other parameters, we have a problem.
                            # But for linear models, term should depend only on data variables.
                            raise ValueError(f"Term for {p} depends on unknown symbol {s}")

                    if not t_args:
                        # Constant term
                        col = np.full_like(y, float(term))
                    else:
                        col = f_term(*t_args)
                        if np.isscalar(col):
                            col = np.full_like(y, col)

                    X_cols.append(col)
                    valid_params.append(p)

                except Exception as e:
                    print(f"Error constructing term for {p} in {eq}: {e}")
                    valid_params = [] # Fail this hypothesis
                    break

            if not valid_params:
                continue

            X = np.column_stack(X_cols)

            # Fit
            try:
                coeffs, residuals, rank, s = lstsq(X, y)
            except Exception as e:
                print(f"Fitting error for {eq}: {e}")
                continue

            y_pred = X @ coeffs
            mse = np.mean((y - y_pred)**2)

            # Reconstruct expression with fitted values
            fitted_rhs = rhs
            for p, val in zip(valid_params, coeffs):
                fitted_rhs = fitted_rhs.subs(p, val)

            fitted_expr = sympy.Eq(lhs, fitted_rhs)

        # 3. Check Tolerance
        if mse > tolerance:
            print(f"Hypothesis DESTROYED: {eq} (MSE={mse:.6f} > {tolerance})")
        else:
            print(f"Hypothesis SAVED: {eq} (MSE={mse:.6f})")
            surviving_hypotheses.append({
                "expression": fitted_expr,
                "mse": mse,
                "original_eq": eq
            })

    return surviving_hypotheses
