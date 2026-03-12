from __future__ import annotations
from pydantic import BaseModel
from typing import Dict, List
from states.task_state import TaskState
from states.step_state import StepState

class GlobalState(BaseModel):
    task_state: TaskState = None
    plan: str = ""
    memories: Dict[str, str] = {}
    step_history: List[StepState] = []