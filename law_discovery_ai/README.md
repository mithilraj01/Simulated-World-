# SimulateDAI: Simulated World Engine

**NOTE: THIS IS A SIMULATED WORLD ENGINE ONLY.**

It does NOT discover laws.
It does NOT contain intelligence.
It is a tool for generating synthetic physical data for external research systems.

## Purpose

The sole purpose of this repository is to:
1. Simulate physical worlds (deterministic, stochastic, chaotic, or biological).
2. Log observations.
3. Export standardized JSON data.

## Supported Worlds

### Deterministic Free Fall
- Particle falling under constant gravity.
- No noise.
- Configurable gravity and initial conditions.

### Stochastic Free Fall
- Particle falling under gravity.
- Gaussian noise added to acceleration dynamics.
- Seed-controlled for reproducibility.

### Chaotic Worlds
- Deterministic logistic map simulator.
- No stochastic noise is used.
- Demonstrates sensitivity to initial conditions.
- No laws or explanations are inferred.
- Provided for external analysis only.

### Biological Worlds (Minimal)
- Minimal biological simulation with agents.
- Agents have energy, age, and simple reproduction rules.
- Selection is emergent from environmental constraints.
- No intelligence, goals, or optimization.
- Used to study discoverability limits under selection and history.
- **Regime:** Biological (cellular/population scale).

## Usage

### Run Deterministic Simulation
```bash
python3 main.py --type deterministic --gravity 9.81
```

### Run Stochastic Simulation
```bash
python3 main.py --type stochastic --noise 0.5
```

### Run Chaotic Simulation
```bash
python3 main.py --type chaotic --r 3.9 --x0 0.5 --timesteps 50
```

### Run Biological Simulation
```bash
python3 main.py --type biological --timesteps 100 --initial_population 20 --grid_size 20
```

### Apply Interventions
Create a JSON file (e.g., `interventions.json`):
```json
[
  {
    "time": 2.0,
    "parameter": "gravity",
    "new_value": 1.62
  }
]
```

Run with interventions:
```bash
python3 main.py --interventions interventions.json
```

## Output

All simulations are exported to the `exports/` directory as JSON files.
The schema includes:
- `world_id`: Unique ID.
- `parameters`: Simulation config.
- `time_series`: List of state observations.
- `interventions`: Applied interventions.
- `noise_model`: Description of noise (if any).
