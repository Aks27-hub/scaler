from pydantic import BaseModel
from typing import List, Optional

class TrafficState(BaseModel):
    cars_per_lane: List[int]
    wait_time_per_lane: List[float]
    current_signal: str
    signal_timer: int
    emergency_present: bool
    emergency_lane: Optional[str]

class TrafficAction(BaseModel):
    action: int

class StepResult(BaseModel):
    state: TrafficState
    reward: float
    done: bool
    info: dict
