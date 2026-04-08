class HardTask:
    def __init__(self):
        self.config = {
            "max_cars_per_lane": 20,
            "arrival_rate": [0.9, 0.8, 0.7, 0.9],
            "emergency_prob": 0.05,
            "no_emergency": False,
            "max_steps": 300,
            "random_seed": 42
        }

    def get_config(self):
        return self.config

def grade_hard(trajectory):
    if not trajectory:
        return 0.0
    info = trajectory[-1].get("info", {})
    arrived = info.get("total_cars_arrived", 1)
    if arrived == 0:
        arrived = 1
    cleared = info.get("total_cars_cleared", 0)
    throughput = cleared / arrived
    
    base_score = max(0.0, min(1.0, throughput))
    
    total_emergencies = info.get("total_emergencies_arrived", 0)
    cleared_under_5 = info.get("emergencies_cleared_under_5", 0)
    
    emergency_bonus = 0.2 if (total_emergencies > 0 and cleared_under_5 == total_emergencies) else 0.0
    emergency_penalty = -0.3 if info.get("emergency_waited_over_10", False) else 0.0
    
    final = base_score + emergency_bonus + emergency_penalty
    return max(0.0, min(1.0, final))
