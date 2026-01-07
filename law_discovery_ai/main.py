import sys
import os
import json
import argparse
import time

# Ensure we can import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from simulators.physics_deterministic.free_fall import run_simulator
from simulators.physics_stochastic.stochastic_free_fall import run_stochastic_simulator

def main():
    parser = argparse.ArgumentParser(description="SimulateDAI: World Generator")
    parser.add_argument("--type", choices=["deterministic", "stochastic"], default="deterministic", help="Type of world to simulate")
    parser.add_argument("--gravity", type=float, default=9.81, help="Gravity constant")
    parser.add_argument("--noise", type=float, default=0.1, help="Noise std (stochastic only)")
    parser.add_argument("--interventions", type=str, default=None, help="Path to JSON file with interventions")

    args = parser.parse_args()

    # Load interventions if provided
    interventions = []
    if args.interventions:
        try:
            with open(args.interventions, 'r') as f:
                interventions = json.load(f)
        except Exception as e:
            print(f"Error loading interventions: {e}")
            return

    print(f"Generating {args.type} world...")

    if args.type == "deterministic":
        world_data = run_simulator(gravity=args.gravity, interventions=interventions)
    else:
        world_data = run_stochastic_simulator(gravity=args.gravity, noise_std=args.noise, interventions=interventions)

    # Export
    exports_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "exports")
    os.makedirs(exports_dir, exist_ok=True)

    filename = f"world_{world_data['world_id']}_{int(time.time())}.json"
    filepath = os.path.join(exports_dir, filename)

    with open(filepath, 'w') as f:
        json.dump(world_data, f, indent=2)

    print(f"World generated and exported to {filepath}")

if __name__ == "__main__":
    main()
