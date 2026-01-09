import uuid
import numpy as np
from ..world_export import export_world

def run_biological_simulator(
    timesteps=50,
    initial_population=10,
    grid_size=10,
    resource_regen_rate=0.1,
    mutation_rate=0.01,
    seed=42,
    interventions=None
):
    """
    Simulates a minimal biological world with agents, energy, and reproduction.

    Args:
        timesteps (int): Number of steps to simulate.
        initial_population (int): Starting number of agents.
        grid_size (int): Size of the 1D resource grid.
        resource_regen_rate (float): Rate at which resources replenish.
        mutation_rate (float): Standard deviation for mutation of traits (if any).
        seed (int): Random seed.
        interventions (list): List of interventions.

    Returns:
        dict: Standardized world dictionary.
    """
    if interventions is None:
        interventions = []

    np.random.seed(seed)

    # Sort interventions
    sorted_interventions = sorted(interventions, key=lambda x: x["time"])
    intervention_idx = 0

    # Environment initialization
    # 1D Grid of resources: [0, 1]
    resources = np.ones(grid_size)
    temperature = 1.0 # State variable affecting metabolic rate

    # Agent initialization
    # Agents: list of dicts
    # Properties: id, x (position), energy, age, alive
    agents = []
    next_agent_id = 0

    for _ in range(initial_population):
        agents.append({
            "id": next_agent_id,
            "x": np.random.randint(0, grid_size),
            "energy": 1.0,
            "age": 0,
            "alive": True
        })
        next_agent_id += 1

    time_series = []
    current_time = 0

    # Regime Descriptor
    regime_descriptor = {
        "regime": "biological",
        "valid_scales": {
            "length": {"min": "cellular", "max": "local population"},
            "time": {"min": "generation", "max": "many generations"},
            "energy": {"min": "metabolic", "max": "environmental"}
        },
        "state_representation": "agent_population",
        "fidelity_limits": "No molecular biology, no genetics, no cognition; selection is emergent only",
        "handoff_rules": {
            "to_regime": "statistical",
            "conditions": "Population-level aggregation or loss of individual resolution"
        }
    }

    parameters = {
        "timesteps": timesteps,
        "initial_population": initial_population,
        "grid_size": grid_size,
        "resource_regen_rate": resource_regen_rate,
        "mutation_rate": mutation_rate,
        "seed": seed,
        "regime_descriptor": regime_descriptor
    }

    # Log initial state
    # We aggregate agent stats for the main state variables to keep schema simple
    # But detailed agent data can be in a dedicated key or just embedded?
    # Prompt says: "Export exactly the same schema as other worlds PLUS: agent population snapshots, aggregate statistics"
    # But export_world enforces specific keys.
    # The prompt says "Export exactly the same schema... PLUS".
    # This implies I might need to extend what export_world accepts OR put it in 'state_variables' / 'time_series'.
    # I will put aggregate stats in time_series entries.
    # I will put full agent dump in 'time_series' under a key 'agents'.

    def get_snapshot(t, res, temp, pop):
        living_pop = [a for a in pop if a["alive"]]
        count = len(living_pop)
        avg_energy = np.mean([a["energy"] for a in living_pop]) if count > 0 else 0.0
        return {
            "time_step": t,
            "temperature": temp,
            "population_count": count,
            "average_energy": avg_energy,
            "resource_level": np.mean(res),
            "agents": [a.copy() for a in living_pop] # Snapshot of living agents
        }

    time_series.append(get_snapshot(current_time, resources, temperature, agents))

    while current_time < timesteps:
        next_time = current_time + 1

        # Process Interventions
        # Interventions happen at the start of the step logic (before dynamics)
        while intervention_idx < len(sorted_interventions):
            intv = sorted_interventions[intervention_idx]
            intv_time = intv["time"]

            if intv_time <= next_time: # Apply if due
                # Applying intervention
                param = intv["parameter"]
                val = intv["new_value"]

                if param == "temperature":
                    temperature = val
                elif param == "resource_regen_rate":
                    resource_regen_rate = val
                elif param == "kill_fraction":
                    # Mass extinction event
                    # Kill fraction of agents
                    living = [a for a in agents if a["alive"]]
                    num_kill = int(len(living) * val)
                    to_kill = np.random.choice(len(living), num_kill, replace=False)
                    for i in to_kill:
                        living[i]["alive"] = False

                intervention_idx += 1
            else:
                break

        # Dynamics

        # 1. Resource Regeneration
        resources += resource_regen_rate
        resources = np.clip(resources, 0.0, 1.0) # Cap at 1.0

        # 2. Agent Actions (Move, Eat, Metabolize, Die, Reproduce)
        new_agents = []

        for agent in agents:
            if not agent["alive"]:
                continue

            # Age
            agent["age"] += 1

            # Metabolize
            # Base cost + temperature penalty (e.g. away from ideal 1.0)
            metabolic_cost = 0.01 * (1.0 + abs(temperature - 1.0))
            agent["energy"] -= metabolic_cost

            # Move (Random Walk)
            move = np.random.choice([-1, 0, 1])
            agent["x"] = (agent["x"] + move) % grid_size

            # Eat
            # Consume resource at location
            loc = agent["x"]
            available = resources[loc]
            consumption = min(available, 0.05) # Max consume 0.05
            agent["energy"] += consumption
            resources[loc] -= consumption

            # Death
            if agent["energy"] <= 0 or agent["age"] > 100:
                agent["alive"] = False
                continue

            # Reproduction
            # Threshold 1.5 energy
            if agent["energy"] > 1.5:
                # Split energy
                agent["energy"] /= 2.0
                offspring = {
                    "id": next_agent_id,
                    "x": agent["x"], # Same location
                    "energy": agent["energy"], # Inherits half
                    "age": 0,
                    "alive": True
                }
                next_agent_id += 1
                new_agents.append(offspring)

        agents.extend(new_agents)

        # Clean up dead agents from main list to keep memory low?
        # Or keep them for history?
        # "lineage extinction" implies history matters.
        # But for "agent population snapshots", prompt says "agents population snapshots".
        # I will keep only living agents in the simulation loop for efficiency,
        # but simulation state technically includes dead ones until they rot.
        # "agents die if energy <= 0".
        # I'll just filter `agents` list to keep living ones for next step to mimic population dynamics.
        agents = [a for a in agents if a["alive"]]

        current_time = next_time
        time_series.append(get_snapshot(current_time, resources, temperature, agents))

    world_id = str(uuid.uuid4())

    state_variables = ["time_step", "temperature", "population_count", "average_energy", "resource_level", "agents"]

    return export_world(
        world_id=world_id,
        world_type="biological_agents_minimal",
        parameters=parameters,
        state_variables=state_variables,
        time_series=time_series,
        interventions=interventions,
        noise_model="Stochastic agent behavior and resource consumption",
        notes="Minimal biological simulation; emergent selection; no intelligence."
    )
