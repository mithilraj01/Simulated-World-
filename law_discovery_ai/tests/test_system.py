import unittest
import sys
import os
import json
import numpy as np

# Add the parent directory to sys.path to allow imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from simulators.physics_deterministic.free_fall import run_simulator
from simulators.physics_stochastic.stochastic_free_fall import run_stochastic_simulator
from simulators.physics_chaotic.logistic_map import run_logistic_map

class TestSimulateDAI(unittest.TestCase):

    def test_deterministic_simulator(self):
        """Verify deterministic simulator output structure and values."""
        output = run_simulator(time_step=1.0, total_time=2.0, gravity=9.81)

        self.assertEqual(output["world_type"], "deterministic")
        self.assertIn("time_series", output)
        self.assertIsNone(output["noise_model"])

        ts = output["time_series"]
        self.assertAlmostEqual(ts[0]["position"], 0.0)
        self.assertAlmostEqual(ts[1]["position"], -4.905)
        self.assertAlmostEqual(ts[2]["position"], -19.62)

    def test_stochastic_simulator(self):
        """Verify stochastic simulator output."""
        output = run_stochastic_simulator(time_step=1.0, total_time=2.0, noise_std=0.0)

        self.assertEqual(output["world_type"], "stochastic")
        self.assertIn("Gaussian", output["noise_model"])

        # With 0 noise, should match deterministic
        ts = output["time_series"]
        self.assertAlmostEqual(ts[1]["position"], -4.905)

    def test_interventions(self):
        """Verify interventions are applied."""
        interventions = [{"time": 1.0, "parameter": "gravity", "new_value": 0.0}]
        output = run_simulator(time_step=1.0, total_time=3.0, gravity=10.0, interventions=interventions)

        ts = output["time_series"]
        # t=0: x=0, v=0, a=-10
        # t=1: x=-5, v=-10. Intervention happens here.
        # Next step (t=1 to t=2): gravity is 0. a=0.
        acc_at_2 = ts[2]["acceleration"]
        self.assertEqual(acc_at_2, 0.0)

    def test_chaotic_simulator(self):
        """Verify chaotic logistic map simulator."""
        # Test basic determinism
        output1 = run_logistic_map(r=3.9, x0=0.5, timesteps=10)
        output2 = run_logistic_map(r=3.9, x0=0.5, timesteps=10)

        self.assertEqual(output1["world_type"], "chaotic")
        self.assertEqual(output1["parameters"]["r"], 3.9)
        self.assertEqual(len(output1["time_series"]), 11) # t=0 to t=10

        # Exact match for reproducibility
        self.assertEqual(output1["time_series"], output2["time_series"])

        # Verify calculation for first step
        # x1 = r * x0 * (1 - x0) = 3.9 * 0.5 * 0.5 = 3.9 * 0.25 = 0.975
        x1 = output1["time_series"][1]["x"]
        self.assertAlmostEqual(x1, 0.975)

    def test_chaotic_sensitivity(self):
        """Verify sensitivity to initial conditions (structural check)."""
        # Increase timesteps to ensure divergence
        output1 = run_logistic_map(r=3.9, x0=0.500000, timesteps=50)
        output2 = run_logistic_map(r=3.9, x0=0.500001, timesteps=50)

        # Should diverge significantly by step 50
        x_end_1 = output1["time_series"][-1]["x"]
        x_end_2 = output2["time_series"][-1]["x"]

        self.assertNotAlmostEqual(x_end_1, x_end_2, places=2)

    def test_chaotic_intervention(self):
        """Verify intervention in chaotic world."""
        # Intervention at t=5, set x=0.5
        interventions = [{"time": 5, "parameter": "x", "new_value": 0.5}]
        output = run_logistic_map(r=3.9, x0=0.2, timesteps=10, interventions=interventions)

        ts = output["time_series"]

        # Check value at t=5
        self.assertEqual(ts[5]["x"], 0.5)

        # Check value at t=6
        # Should follow from x=0.5: x6 = 3.9 * 0.5 * 0.5 = 0.975
        self.assertAlmostEqual(ts[6]["x"], 0.975)

    def test_export_schema(self):
        """Verify export keys."""
        output = run_simulator()
        required_keys = ["world_id", "world_type", "parameters", "state_variables", "time_series", "interventions", "noise_model", "notes"]
        for key in required_keys:
            self.assertIn(key, output)

if __name__ == '__main__':
    unittest.main()
