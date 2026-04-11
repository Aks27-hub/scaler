class MediumTask:
    def __init__(self):
        self.config = {
            "max_cars_per_lane": 10,
            "arrival_rate": [0.6, 0.2, 0.5, 0.3],
            "no_emergency": True,
            "max_steps": 200,
            "random_seed": 42,
        }

    def get_config(self):
        return self.config

    def grade(self, *args, **kwargs):
        return grade_medium(*args, **kwargs)


def _strict_unit_interval(score: float) -> float:
    low = 0.06
    high = 0.94
    try:
        numeric = float(score)
    except Exception:
        numeric = 0.5
    return min(high, max(low, numeric))


def _extract_trajectory(*args, **kwargs):
    if "trajectory" in kwargs:
        return kwargs.get("trajectory")
    if args:
        first = args[0]
        if isinstance(first, dict):
            if "trajectory" in first:
                return first.get("trajectory")
            if "episodes" in first:
                episodes = first.get("episodes")
                if isinstance(episodes, list) and episodes:
                    return episodes[-1]
        return first
    return None


def grade_medium(*args, **kwargs):
    trajectory = _extract_trajectory(*args, **kwargs)
    if not isinstance(trajectory, list) or not trajectory:
        return _strict_unit_interval(0.0)

    last = trajectory[-1] if isinstance(trajectory[-1], dict) else {}
    info = last.get("info", {}) if isinstance(last, dict) else {}
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

    return _strict_unit_interval(score)


def grade(*args, **kwargs):
    return grade_medium(*args, **kwargs)