from __future__ import annotations
from pydantic import BaseModel
from states.agent_state import AgentState
from states.env_state import EnvState

class StepState(BaseModel):
    step_id: int = 0
    env_state: EnvState
    agent_state: AgentState