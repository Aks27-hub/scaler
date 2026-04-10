---
title: Autonomous Traffic Control
emoji: "🚦"
colorFrom: red
colorTo: blue
sdk: docker
sdk_version: "latest"
python_version: "3.11"
app_file: app.py
pinned: false
---

# Autonomous Traffic Control System

## 1. Problem Description
This environment models a real-world traffic signal control scenario at an intersection. The goal is to build an autonomous agent that can optimize traffic flow by strategically managing a set of signal lights. The agent must aim to clear queues quickly while avoiding starvation and reacting dynamically to the arrival of emergency vehicles to ensure they are expedited through the intersection.

## 2. State Space
The current state is a comprehensive snapshot of the intersection. It includes the following fields:
- `cars_per_lane` (array of `int`): The current number of cars queued in each lane (ordered N, S, E, W).
- `wait_time_per_lane` (array of `float`): The average wait time (in seconds/steps) of vehicles queued per lane.
- `current_signal` (`string`): The phase that is currently green. Either `"NS"` (North-South) or `"EW"` (East-West).
- `signal_timer` (`int`): The number of consecutive steps the current signal has been green without a switch.
- `emergency_present` (`bool`): Indicates whether an emergency vehicle is currently present in the queues.
- `emergency_lane` (`string` or `null`): The specific lane where the emergency vehicle is located (if any).

## 3. Action Space
The agent receives discrete observations and takes discrete actions (0-2):
- `0` - **Hold**: Maintain the current signal phase without changing it.
- `1` - **Switch**: Switch the traffic signal state (i.e. from NS to EW, or EW to NS).
- `2` - **Emergency Override**: Immediately set the signal to green for the phase containing the emergency vehicle. If no emergency vehicle is present, this action operates like a signal switch.

## 4. Reward Logic
The reinforcement learning environment leverages dense positive and negative reward signals to guide training.
**Positive rewards:**
- `+0.5` per car that effectively crosses the intersection and exits the environment during the action step.
- `+2.0` if an emergency vehicle successfully exits the environment.
- `+0.3` if the average wait time across all lanes decreased after the step.
- `+0.1` if the traffic imbalance (maximum queue length minus minimum queue length) decreased.

**Negative rewards:**
- `-0.2` per vehicle still queuing (scaled efficiently by average wait time per vehicle).
- `-1.0` (starvation penalty) for every step a lane remains red beyond 10 consecutive steps.
- `-3.0` severely penalizes the agent if an emergency vehicle has waited more than 5 steps without experiencing an override.

## 5. Task Descriptions
The environment provides three grading tracks based on difficulty:

### Easy Task (easy_task.py)
Config: 2 lanes (N-S), no emergency vehicles, 0.3 arrival rate.
Difficulty: Trivial optimization to prevent starvation across two lanes.
Grading: Full marks (1.0) for maintaining average vehicle wait time under 5 steps. Partially grades 0.7 (<10 steps) and 0.4 (<20 steps).

### Medium Task (medium_task.py)
Config: Full 4-lane intersection (N, S, E, W), uneven arrival rates, no emergency vehicles. Max 200 steps.
Difficulty: Agents must prioritize high-traffic lanes systematically while preventing starvation.
Grading: Bases score extensively on throughput percentage (cleared cars / arrived cars). Applies a -0.1 reduction if severe starvation (>15 red steps) occurs. Score intervals: 1.0 (>0.85 throughput), 0.7 (>0.65), 0.4 (>0.45).

### Hard Task (hard_task.py)
Config: Complete chaotic simulation with 0.9 arrival rates consistently, maximum queues, and 0.05 emergency vehicle spawn probability per step. Requires rigorous priority routing and emergency handling over 300 steps.
Difficulty: The agent must override for emergency vehicles rapidly without cascading queue disasters.
Grading: Score is base throughput clamped alongside strict emergency bonuses (+0.2 if *all* emergency vehicles are cleared within 5 steps) and penalties (-0.3 if *any* emergency vehicle waits above 10 steps). Max score ranges [0.0, 1.0].

## 6. Setup Instructions

**Local Python Setup:**
```bash
pip install -r requirements.txt
python inference.py
uvicorn app:app --host 0.0.0.0 --port 7860
```

**Docker Setup:**
```bash
docker build -t traffic-control .
docker run -p 7860:7860 traffic-control
```

## 7. Environment Variables
To authenticate LLM inferences efficiently, the agent (`inference.py`) queries these credentials heavily:
- `API_BASE_URL`: Full base host prefix directing to inference (e.g. `http://localhost:8000/v1`)
- `MODEL_NAME`: Hugging Face/OpenAI deployed reference model ID strings.
- `HF_TOKEN`: API Token credentials corresponding to authorized users.
