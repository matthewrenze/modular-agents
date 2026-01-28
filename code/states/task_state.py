from __future__ import annotations
from pydantic import BaseModel

class TaskState(BaseModel):
    task: str = ""
    step_id: int = 0
    max_steps: int = 0
    max_items: int = 0
    max_score: int = 0
    max_reward: float = 1.0
    success: bool = False