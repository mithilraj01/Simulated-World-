import sys
import os
import json
import argparse
import time

# Ensure we can import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from simulators.physics_deterministic.free_fall import run_simulator
from simulators.physics_stochastic.stochastic_free_fall import run_stochastic_simulator
from simulators.physics_chaotic.logistic_map import run_logistic_map
from simulators.biological_agents_minimal.agent_simulator import run_biological_simulator
from simulators.ocean_column_vertical.ocean_simulator import run_ocean_simulator

def main():
    parser = argparse.ArgumentParser(description="SimulateDAI: World Generator")
    parser.add_argument("--type", choices=["deterministic", "stochastic", "chaotic", "biological", "ocean"], default="deterministic", help="Type of world to simulate")

    # Physics parameters
    parser.add_argument("--gravity", type=float, default=9.81, help="Gravity constant (deterministic/stochastic)")
    parser.add_argument("--noise", type=float, default=0.1, help="Noise std (stochastic only)")

    # Chaos parameters
    parser.add_argument("--r", type=float, default=3.9, help="Control parameter r (chaotic only)")
    parser.add_argument("--x0", type=float, default=0.5, help="Initial value x0 (chaotic only)")

    # Biological/Ocean parameters
    parser.add_argument("--timesteps", type=int, default=100, help="Number of timesteps")
    parser.add_argument("--initial_population", type=int, default=10, help="Initial population (biological only)")
    parser.add_argument("--grid_size", type=int, default=10, help="Grid size (biological only)")
    parser.add_argument("--regen_rate", type=float, default=0.1, help="Resource regen rate (biological only)")

    # Ocean parameters
    parser.add_argument("--depth_layers", type=int, default=10, help="Number of depth layers (ocean only)")
    parser.add_argument("--surface_temp", type=float, default=20.0, help="Surface temperature (ocean only)")
    parser.add_argument("--bottom_temp", type=float, default=4.0, help="Bottom temperature (ocean only)")
    parser.add_argument("--diffusion_rate", type=float, default=0.1, help="Diffusion rate (ocean only)")

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
    elif args.type == "stochastic":
        world_data = run_stochastic_simulator(gravity=args.gravity, noise_std=args.noise, interventions=interventions)
    elif args.type == "chaotic":
        world_data = run_logistic_map(r=args.r, x0=args.x0, timesteps=args.timesteps, interventions=interventions)
    elif args.type == "biological":
        world_data = run_biological_simulator(
            timesteps=args.timesteps,
            initial_population=args.initial_population,
            grid_size=args.grid_size,
            resource_regen_rate=args.regen_rate,
            seed=42,
            interventions=interventions
        )
    elif args.type == "ocean":
        world_data = run_ocean_simulator(
            timesteps=args.timesteps,
            depth_layers=args.depth_layers,
            surface_temp=args.surface_temp,
            bottom_temp=args.bottom_temp,
            diffusion_rate=args.diffusion_rate,
            seed=42,
            interventions=interventions
        )

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
