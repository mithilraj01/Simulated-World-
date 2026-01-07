# SimulateDAI

## Overview
SimulateDAI is a scientific system designed to discover physical laws from simulated data. It simulates simple physical worlds, observes them, generates symbolic hypotheses, attempts to falsify them, and selects the best "law" using Minimum Description Length (MDL) principles.

## Execution Flow
1. **Simulation**: A deterministic physical world (e.g., free fall) is simulated to generate ground truth data.
2. **Encoding**: The raw simulation output is encoded into a standardized numerical format.
3. **Hypothesis Generation**: A symbolic generator produces a list of candidate equations (linear combinations, polynomials) that might explain the data.
4. **Falsification**: Each hypothesis is evaluated against the observed data. Hypotheses with high error are discarded.
5. **MDL Selection**: The surviving hypotheses are ranked based on Description Length (complexity + error). The best one is selected as the discovered law.

## Disclaimer
This is a backend research prototype, not a production product. It does not include a UI or advanced intelligence features.
