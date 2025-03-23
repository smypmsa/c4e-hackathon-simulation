# UPDATED: ADDED CALL TO LOCAL FETCH.AI AGENT TO GET DECISION
---
---

# energy-ai-agents-simulation/README.md

# Energy AI Agents Simulation

This project implements agent-based modeling techniques using local Fetch.ai agents to simulate complex interactions between community members. The simulation aims to explore how individual behaviors and interactions can impact community dynamics and resource management.

## Project Structure

```
energy-ai-agents-simulation
├── src
│   ├── agents
│   │   ├── __init__.py
│   │   ├── community_agent.py
│   │   └── member_agent.py
│   ├── models
│   │   ├── __init__.py
│   │   ├── community.py
│   │   └── member.py
│   ├── simulation
│   │   ├── __init__.py
│   │   └── run_simulation.py
│   └── utils
│       ├── __init__.py
│       └── helper_functions.py
├── requirements.txt
└── README.md
```

## Setup Instructions

1. Clone the repository:
   ```
   git clone <repository-url>
   cd energy-ai-agents-simulation
   ```

2. create or load venv in python
   ```
   source venv/bin/activate


3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

4. add src to PYTHONPATH
   ```
   export PYTHONPATH=$PYTHONPATH:$(pwd)/src
   ```

## Usage

To run the simulation, execute the following command:
```
python3 src/simulation/energy_community_simulation.py storages.csv pv_profiles_2_days logs grid_costs
```

This will initialize the community and agents, run the simulation for a specified number of time steps, and collect data for analysis.

## Overview of Agent-Based Modeling

Agent-based modeling (ABM) is a computational modeling approach that simulates the actions and interactions of autonomous agents to assess their effects on the system as a whole. In this project, agents represent community members who interact with each other and their environment, making decisions based on their states and the dynamics of the community.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.
