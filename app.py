import math
from typing import Any, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from traffic_env import TrafficEnv
from models import TrafficState, TrafficAction, StepResult
from easy_task import EasyTask, grade_easy
from medium_task import MediumTask, grade_medium
from hard_task import HardTask, grade_hard

app = FastAPI()
env = TrafficEnv()  # Single global env instance

TASKS = {
    "easy": EasyTask,
    "medium": MediumTask,
    "hard": HardTask,
}

GRADERS = {
    "easy": grade_easy,
    "medium": grade_medium,
    "hard": grade_hard,
}

_SCORE_EPS = 1e-6


def _clamp_score(score) -> float:
    """Guarantee score is strictly in the open interval (0, 1)."""
    try:
        v = float(score)
    except Exception:
        v = 0.5
    if not math.isfinite(v):
        v = 0.5
    return min(1.0 - _SCORE_EPS, max(_SCORE_EPS, v))


class GradeRequest(BaseModel):
    task_id: str
    trajectory: Optional[List[Any]] = None


class GradeResponse(BaseModel):
    task_id: str
    score: float
    valid: bool


@app.get("/")
def root():
    return {"status": "ok", "message": "Autonomous Traffic Control API is running"}


@app.post("/reset", response_model=TrafficState)
def reset(payload: Optional[dict[str, Any]] = None):
    global env
    if payload:
        task_key = payload.get("task_id") or payload.get("task") or payload.get("id")
        if isinstance(task_key, int):
            task_key = ["easy", "medium", "hard"][task_key] if 0 <= task_key <= 2 else None

        task_cls = TASKS.get(str(task_key)) if task_key is not None else None
        if task_cls is not None:
            config = task_cls().get_config()
            seed = payload.get("seed")
            if isinstance(seed, int):
                config["random_seed"] = seed
            env = TrafficEnv(config)

    state = env.reset()
    return state


@app.post("/step", response_model=StepResult)
def step(action: TrafficAction):
    state, reward, done, info = env.step(action.action)
    return StepResult(state=state, reward=reward, done=done, info=info)


@app.get("/state", response_model=TrafficState)
def get_state():
    return env.state()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/grade", response_model=GradeResponse)
def grade(request: GradeRequest):
    """
    Grade a completed task trajectory.
    Accepts { task_id: str, trajectory: list } and returns a score
    strictly in the open interval (0, 1) as required by the platform.
    """
    task_key = str(request.task_id).lower().strip()

    # Accept numeric task IDs (0=easy, 1=medium, 2=hard)
    if task_key.isdigit():
        task_key = ["easy", "medium", "hard"][int(task_key)] if int(task_key) <= 2 else task_key

    if task_key not in GRADERS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown task_id '{task_key}'. Must be one of: {list(GRADERS.keys())}",
        )

    grader = GRADERS[task_key]
    trajectory = request.trajectory or []
    raw_score = grader(trajectory)
    score = _clamp_score(raw_score)

    return GradeResponse(
        task_id=task_key,
        score=score,
        valid=True,
    )


# Alias: some platform runners POST to /score instead of /grade
@app.post("/score", response_model=GradeResponse)
def score_alias(request: GradeRequest):
    return grade(request)

