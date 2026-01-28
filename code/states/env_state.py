from __future__ import annotations
from pydantic import BaseModel

class EnvState(BaseModel):
    feedback: str = ""
    location: str = ""
    description: str = ""
    inventory: str = ""
    items: int = 0
    score: int = 0
    reward: float = 0.0
    is_done: bool = False