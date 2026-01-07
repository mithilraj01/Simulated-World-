import sys
import os

# Ensure we can import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from simulators.physics_deterministic.free_fall import run_simulator
from encoder.observation_encoder import encode_observations
from hypothesis.symbolic_generator import generate_hypotheses
from falsifier.falsifier import falsify_hypotheses
from mdl.mdl_selector import select_best_law

def main():
    print("--- Phase 1: Simulate World ---")
    sim_output = run_simulator(time_step=0.1, total_time=5.0, initial_position=0.0, initial_velocity=0.0)
    print(f"Simulation complete. {len(sim_output['time_series'])} steps generated.")
    print(f"Ground Truth: {sim_output['ground_truth_law']}")

    print("\n--- Phase 2: Encode Observations ---")
    encoded_data = encode_observations(sim_output)
    print(f"Encoded variables: {encoded_data['variables']}")
    print(f"Data matrix shape: {encoded_data['data_matrix'].shape}")

    print("\n--- Phase 3: Generate Hypotheses ---")
    hypotheses = generate_hypotheses()
    print(f"Generated {len(hypotheses)} candidates:")
    for h in hypotheses:
        print(f"  - {h}")

    print("\n--- Phase 4: Falsify Hypotheses ---")
    # Tolerance for float errors (since we use exact math, error should be near 0, but numerical noise exists)
    survivors = falsify_hypotheses(encoded_data, hypotheses, tolerance=1e-10)
    print(f"Surviving hypotheses: {len(survivors)}")

    print("\n--- Phase 5: MDL Selection ---")
    result = select_best_law(survivors)

    print("\n--- FINAL RESULT ---")
    print(f"Outcome: {result['result']}")
    if result['result'] == "LAW":
        print(f"Discovered Law: {result['expression']}")
        print(f"Description Length: {result['description_length']}")
    else:
        print("No compact law found.")

if __name__ == "__main__":
    main()
