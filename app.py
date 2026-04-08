from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from traffic_env import TrafficEnv
from models import TrafficState, TrafficAction, StepResult
from easy_task import EasyTask
from medium_task import MediumTask
from hard_task import HardTask

app = FastAPI()
env = TrafficEnv() # Single global env instance


class ResetRequest(BaseModel):
    task_id: Optional[str] = None
    seed: Optional[int] = None


TASKS = {
    "easy": EasyTask,
    "medium": MediumTask,
    "hard": HardTask,
}

@app.post("/reset", response_model=TrafficState)
def reset(payload: Optional[ResetRequest] = None):
    global env
    if payload and payload.task_id:
        task_cls = TASKS.get(payload.task_id)
        if task_cls is None:
            raise HTTPException(status_code=400, detail=f"Unknown task_id: {payload.task_id}")
        config = task_cls().get_config()
        if payload.seed is not None:
            config["random_seed"] = payload.seed
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
