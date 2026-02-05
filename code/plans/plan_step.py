from __future__ import annotations
from pydantic import BaseModel

class PlanStep(BaseModel):
    id: int = 0
    status: str = "todo"
    label: str = ""