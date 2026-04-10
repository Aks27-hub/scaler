class EasyTask:
    def __init__(self):
        self.config = {
            "max_cars_per_lane": 5,
            "arrival_rate": 0.3,
            "no_emergency": True,
            "max_steps": 100,
            "random_seed": 42
        }

    def get_config(self):
        return self.config


def _strict_unit_interval(score: float) -> float:
    eps = 1e-6
    return min(1.0 - eps, max(eps, score))


def grade_easy(trajectory):
    if not trajectory:
        return _strict_unit_interval(0.0)
    info = trajectory[-1].get("info", {})
    waits = info.get("all_cars_wait_times", [])
    if not waits:
        return _strict_unit_interval(1.0)
    avg_wait = sum(waits) / len(waits)
    if avg_wait < 5.0:
        return _strict_unit_interval(1.0)
    elif avg_wait < 10.0:
        return _strict_unit_interval(0.7)
    elif avg_wait < 20.0:
        return _strict_unit_interval(0.4)
    else:
        return _strict_unit_interval(0.0)