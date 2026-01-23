from __future__ import annotations
from pydantic import BaseModel
from typing import List
from states.step_state import StepState

class GlobalState(BaseModel):
    task: str = ""
    current_step_id: int = 0
    step_history: List[StepState] = []