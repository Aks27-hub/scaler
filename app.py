from typing import Any, Optional

from fastapi import FastAPI
from traffic_env import TrafficEnv
from models import TrafficState, TrafficAction, StepResult
from easy_task import EasyTask
from medium_task import MediumTask
from hard_task import HardTask

app = FastAPI()
env = TrafficEnv() # Single global env instance


TASKS = {
    "easy": EasyTask,
    "medium": MediumTask,
    "hard": HardTask,
}


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
