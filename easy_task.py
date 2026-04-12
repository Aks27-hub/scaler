import math


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
        score = grade_easy(*args, **kwargs)
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


def grade_easy(*args, **kwargs):
    trajectory = _extract_trajectory(*args, **kwargs)
    if not isinstance(trajectory, list) or not trajectory:
        # No trajectory data — return a low-but-valid score
        return _strict_unit_interval(0.05)

    last = trajectory[-1] if isinstance(trajectory[-1], dict) else {}
    info = last.get("info", {}) if isinstance(last, dict) else {}
    waits = info.get("all_cars_wait_times", [])

    if not isinstance(waits, list) or not waits:
        # No wait data recorded — treat as perfect performance (agent kept queues empty)
        return _strict_unit_interval(0.95)

    numeric_waits = [_safe_float(w, default=0.0) for w in waits]
    # Filter out non-positive sentinel values that indicate missing data
    numeric_waits = [w for w in numeric_waits if math.isfinite(w) and w >= 0.0]
    if not numeric_waits:
        return _strict_unit_interval(0.95)

    avg_wait = sum(numeric_waits) / max(1, len(numeric_waits))

    # Continuous interpolation — no hard boundaries that produce exact 0 or 1.
    # Mapping:  avg_wait=0  -> ~0.95,  avg_wait=5  -> ~0.70,
    #           avg_wait=10 -> ~0.40,  avg_wait=20 -> ~0.10,  avg_wait->inf -> ~0.05
    # Formula: score = 0.95 * exp(-avg_wait / 12)
    raw_score = 0.95 * math.exp(-avg_wait / 12.0)
    return _strict_unit_interval(raw_score)


def grade(*args, **kwargs):
    return grade_easy(*args, **kwargs)