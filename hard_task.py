import math


class HardTask:
    def __init__(self):
        self.config = {
            "max_cars_per_lane": 20,
            "arrival_rate": [0.9, 0.8, 0.7, 0.9],
            "emergency_prob": 0.05,
            "no_emergency": False,
            "max_steps": 300,
            "random_seed": 42,
        }

    def get_config(self):
        return self.config

    def grade(self, *args, **kwargs):
        score = grade_hard(*args, **kwargs)
        # Ensure score is strictly between 0 and 1 (platform requirement)
        return _strict_unit_interval(score)


def _strict_unit_interval(score: float) -> float:
    """Clamp score to the open interval (0, 1) — strictly exclusive of both ends."""
    _EPS = 1e-6
    try:
        numeric = float(score)
    except Exception:
        numeric = 0.5
    if not math.isfinite(numeric):
        numeric = 0.5
    return min(1.0 - _EPS, max(_EPS, numeric))


def _safe_float(value, default=0.0):
    try:
        numeric = float(value)
    except Exception:
        return float(default)
    if not math.isfinite(numeric):
        return float(default)
    return numeric


def _unwrap_trajectory_payload(payload):
    # Tolerate nested payload wrappers used by different runners.
    for _ in range(5):
        if isinstance(payload, dict):
            if "trajectory" in payload:
                payload = payload.get("trajectory")
                continue
            if "episodes" in payload:
                episodes = payload.get("episodes")
                if isinstance(episodes, list) and episodes:
                    payload = episodes[-1]
                    continue
            break
        if isinstance(payload, tuple):
            payload = list(payload)
            break
        break
    return payload


def _extract_trajectory(*args, **kwargs):
    if "trajectory" in kwargs:
        payload = _unwrap_trajectory_payload(kwargs.get("trajectory"))
        if isinstance(payload, list):
            return payload
    if "episodes" in kwargs:
        payload = _unwrap_trajectory_payload({"episodes": kwargs.get("episodes")})
        if isinstance(payload, list):
            return payload
    if args:
        for candidate in args:
            payload = _unwrap_trajectory_payload(candidate)
            if isinstance(payload, list):
                return payload
    return None


def grade_hard(*args, **kwargs):
    trajectory = _extract_trajectory(*args, **kwargs)
    if not isinstance(trajectory, list) or not trajectory:
        # No trajectory data — return a low-but-valid score
        return _strict_unit_interval(0.05)

    last = trajectory[-1] if isinstance(trajectory[-1], dict) else {}
    info = last.get("info", {}) if isinstance(last, dict) else {}
    arrived = _safe_float(info.get("total_cars_arrived", 1), default=1.0)
    if arrived <= 0:
        arrived = 1.0
    cleared = _safe_float(info.get("total_cars_cleared", 0), default=0.0)
    throughput = cleared / arrived

    # Continuous base score in (0.05, 0.95) — cannot be exactly 0 or 1.
    # Formula: base = 0.05 + 0.90 * clamp(throughput, 0, 1)
    base_score = 0.05 + 0.90 * max(0.0, min(1.0, throughput))

    total_emergencies = _safe_float(info.get("total_emergencies_arrived", 0), default=0.0)
    cleared_under_5 = _safe_float(info.get("emergencies_cleared_under_5", 0), default=0.0)

    # Proportional adjustments keep score continuous and bounded.
    # Emergency bonus: +15 % of remaining headroom toward 1 (never reaches 1).
    if total_emergencies > 0 and cleared_under_5 == total_emergencies:
        base_score = base_score + 0.15 * (1.0 - base_score)

    # Emergency penalty: reduce to 80 % of current score (never reaches 0).
    if info.get("emergency_waited_over_10", False):
        base_score = base_score * 0.80

    return _strict_unit_interval(base_score)


def grade(*args, **kwargs):
    return grade_hard(*args, **kwargs)