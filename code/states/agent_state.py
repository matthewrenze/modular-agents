from __future__ import annotations
from pydantic import BaseModel

class AgentState(BaseModel):
    thought: str = ""
    action: str = ""
    summary: str = ""