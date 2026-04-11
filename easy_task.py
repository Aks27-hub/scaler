class EasyTask:
    def __init__(self):
        self.config = {
            "max_cars_per_lane": 5,
            "arrival_rate": 0.3,
            "no_emergency": True,
            "max_steps": 100,
            "random_seed": 42,
        }

    def get_config(self):
        return self.config

    def grade(self, *args, **kwargs):
        return grade_easy(*args, **kwargs)


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


def grade_easy(*args, **kwargs):
    trajectory = _extract_trajectory(*args, **kwargs)
    if not isinstance(trajectory, list) or not trajectory:
        return _strict_unit_interval(0.0)

    last = trajectory[-1] if isinstance(trajectory[-1], dict) else {}
    info = last.get("info", {}) if isinstance(last, dict) else {}
    waits = info.get("all_cars_wait_times", [])

    if not isinstance(waits, list) or not waits:
        return _strict_unit_interval(1.0)

    avg_wait = sum(waits) / max(1, len(waits))
    if avg_wait < 5.0:
        score = 1.0
    elif avg_wait < 10.0:
        score = 0.7
    elif avg_wait < 20.0:
        score = 0.4
    else:
        score = 0.0
    return _strict_unit_interval(score)


def grade(*args, **kwargs):
    return grade_easy(*args, **kwargs)