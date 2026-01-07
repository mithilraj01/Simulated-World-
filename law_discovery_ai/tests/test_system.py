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

class TestSimulateDAI(unittest.TestCase):

    def test_deterministic_simulator(self):
        """Verify deterministic simulator output structure and values."""
        output = run_simulator(time_step=1.0, total_time=2.0, gravity=9.81)

        self.assertEqual(output["world_type"], "deterministic")
        self.assertIn("time_series", output)
        self.assertIsNone(output["noise_model"])

        ts = output["time_series"]
        # Check simple physics: x = -0.5 * g * t^2
        # t=0: x=0
        # t=1: x=-4.905
        # t=2: x=-4.905 * 4
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
        # Intervention: change gravity to 0 at t=1.0
        interventions = [{"time": 1.0, "parameter": "gravity", "new_value": 0.0}]
        output = run_simulator(time_step=1.0, total_time=3.0, gravity=10.0, interventions=interventions)

        ts = output["time_series"]
        # t=0: x=0, v=0, a=-10
        # t=1: x = 0 + 0 - 0.5*10*1^2 = -5. v = -10. Intervention happens here/after step.
        # Next step (t=1 to t=2): gravity is 0. a=0.
        # x = -5 + (-10)*1 + 0 = -15.
        # v = -10 + 0 = -10.

        # Let's check acceleration recorded in logs
        # t=0 log: a=-10 (initial)
        # t=1 log: a=-10 (used for step 0->1) OR a=0 (if updated before log?)
        # My implementation logs state AFTER update loop for t>0.
        # t=1 log is result of step 0->1.

        # Let's check t=2. Step 1->2 used gravity=0.
        # So at t=2, acceleration should be 0.

        # Check acceleration at t=2
        # ts indices: 0->0.0, 1->1.0, 2->2.0
        acc_at_2 = ts[2]["acceleration"]
        self.assertEqual(acc_at_2, 0.0)

    def test_export_schema(self):
        """Verify export keys."""
        output = run_simulator()
        required_keys = ["world_id", "world_type", "parameters", "state_variables", "time_series", "interventions", "noise_model", "notes"]
        for key in required_keys:
            self.assertIn(key, output)

if __name__ == '__main__':
    unittest.main()
