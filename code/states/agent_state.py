from __future__ import annotations
from pydantic import BaseModel

class AgentState(BaseModel):
    summary: str = ""
    plan: str = ""
    memory: str = ""
    thought: str = ""
    action: str = ""