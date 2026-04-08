class MediumTask:
    def __init__(self):
        self.config = {
            "max_cars_per_lane": 10,
            "arrival_rate": [0.6, 0.2, 0.5, 0.3],
            "no_emergency": True,
            "max_steps": 200,
            "random_seed": 42
        }
        
    def get_config(self):
        return self.config

def grade_medium(trajectory):
    if not trajectory:
        return 0.0
    info = trajectory[-1].get("info", {})
    arrived = info.get("total_cars_arrived", 1)
    if arrived == 0:
        arrived = 1
    cleared = info.get("total_cars_cleared", 0)
    throughput = cleared / arrived
    
    score = 0.0
    if throughput > 0.85:
        score = 1.0
    elif throughput > 0.65:
        score = 0.7
    elif throughput > 0.45:
        score = 0.4
        
    if info.get("starvation_occurred", False):
        score -= 0.1
        
    return max(0.0, min(1.0, score))
