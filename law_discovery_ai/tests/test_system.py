import unittest
import sys
import os
import numpy as np
import sympy

# Add the parent directory to sys.path to allow imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from simulators.physics_deterministic.free_fall import run_simulator
from encoder.observation_encoder import encode_observations
from hypothesis.symbolic_generator import generate_hypotheses
from falsifier.falsifier import falsify_hypotheses
from mdl.mdl_selector import select_best_law

class TestSimulateDAI(unittest.TestCase):

    def setUp(self):
        # Common setup if needed
        pass

    def test_simulator_structure(self):
        """Verify simulator output format and deterministic values."""
        output = run_simulator(time_step=1.0, total_time=2.0)

        self.assertIn("state_variables", output)
        self.assertIn("time_series", output)
        self.assertIn("ground_truth_law", output)
        self.assertEqual(output["ground_truth_law"], "x = x0 + v0*t + 0.5*a*t^2")

        # Check values for t=0, t=1, t=2 with g=9.81
        # x = 0 + 0*t + 0.5*(-9.81)*t^2 = -4.905 * t^2
        ts = output["time_series"]
        self.assertEqual(len(ts), 3)

        self.assertAlmostEqual(ts[0]["position"], 0.0)
        self.assertAlmostEqual(ts[1]["position"], -4.905)
        self.assertAlmostEqual(ts[2]["position"], -4.905 * 4)

    def test_encoder(self):
        """Verify encoder produces correct matrix."""
        sim_output = {
            "state_variables": ["a", "b"],
            "time_series": [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
        }
        encoded = encode_observations(sim_output)

        self.assertEqual(encoded["variables"], ["a", "b"])
        expected_matrix = np.array([[1, 2], [3, 4]])
        np.testing.assert_array_equal(encoded["data_matrix"], expected_matrix)

    def test_generator(self):
        """Verify generator produces expected symbolic forms."""
        hyps = generate_hypotheses()
        # We expect 3 hypotheses: Constant, Linear, Quadratic
        self.assertEqual(len(hyps), 3)

        # Check that 'position' and 'time' are in the expressions
        time = sympy.Symbol('time')
        position = sympy.Symbol('position')

        self.assertTrue(any(h.lhs == position for h in hyps))
        self.assertTrue(any(time in h.rhs.free_symbols for h in hyps if h.rhs.free_symbols))

    def test_falsifier_logic(self):
        """Verify falsifier correctly fits and filters hypotheses."""
        # Create synthetic data: y = 2 * t
        variables = ["position", "time"]
        # t = 0, 1, 2, 3
        t_data = np.array([0, 1, 2, 3])
        y_data = 2 * t_data

        data_matrix = np.column_stack([y_data, t_data])

        encoded_data = {
            "variables": variables,
            "data_matrix": data_matrix
        }

        time = sympy.Symbol('time')
        position = sympy.Symbol('position')
        C0, C1 = sympy.symbols('C0 C1')

        # Hypotheses:
        # 1. position = C0 (Should fail)
        # 2. position = C0 + C1 * time (Should pass with C0=0, C1=2)

        h1 = sympy.Eq(position, C0)
        h2 = sympy.Eq(position, C0 + C1 * time)

        hypotheses = [h1, h2]

        survivors = falsify_hypotheses(encoded_data, hypotheses, tolerance=1e-5)

        self.assertEqual(len(survivors), 1)
        self.assertEqual(survivors[0]["original_eq"], h2)
        self.assertAlmostEqual(survivors[0]["mse"], 0.0)

    def test_mdl_selector(self):
        """Verify MDL selector chooses the simplest low-error hypothesis."""
        # Mock survivors
        # H1: simple, low error -> DL low
        # H2: complex, low error -> DL high
        # H3: simple, high error -> DL high

        h1 = {"expression": sympy.sympify("x + 1"), "mse": 0.0}
        h2 = {"expression": sympy.sympify("x**2 + x + 1"), "mse": 0.0}

        # We need to wrap them in a structure expected by select_best_law
        # Actually select_best_law takes a list of dicts

        result = select_best_law([h1, h2])

        # H1 should be preferred because it has fewer ops
        self.assertEqual(result["result"], "LAW")
        self.assertEqual(result["expression"], "x + 1")

if __name__ == '__main__':
    unittest.main()
