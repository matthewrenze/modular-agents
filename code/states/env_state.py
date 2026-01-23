from __future__ import annotations
from pydantic import BaseModel

class EnvState(BaseModel):
    feedback: str = ""
    location: str = ""
    description: str = ""
    inventory: str = ""
    score: int = 0
    max_score: int = 0
    reward: float = 0.0
    max_reward: float = 1.0
    is_done: bool = False