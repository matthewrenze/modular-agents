from __future__ import annotations
from pydantic import BaseModel
from typing import Dict, List
from plans.plan import Plan
from states.task_state import TaskState
from states.step_state import StepState

class GlobalState(BaseModel):
    task_state: TaskState = None
    plan: Plan = []
    memories: Dict[str, str] = {}
    step_history: List[StepState] = []