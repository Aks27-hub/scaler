import math


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
        score = grade_medium(*args, **kwargs)
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


def grade_medium(*args, **kwargs):
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
    throughput = cleared / arrived  # value in [0, 1] for valid runs

    # Continuous interpolation — avoids exact 0 or 1.
    # Mapping: throughput=1.0 -> ~0.95, throughput=0.85 -> ~0.82,
    #          throughput=0.65 -> ~0.62, throughput=0.45 -> ~0.40,
    #          throughput=0   -> ~0.05
    # Formula: base = 0.05 + 0.90 * throughput  (linear in [0.05, 0.95])
    raw_score = 0.05 + 0.90 * max(0.0, min(1.0, throughput))

    # Starvation penalty: reduce by 10 % of current score (stays continuous)
    if info.get("starvation_occurred", False):
        raw_score *= 0.90

    return _strict_unit_interval(raw_score)


def grade(*args, **kwargs):
    return grade_medium(*args, **kwargs)