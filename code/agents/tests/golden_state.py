from states.global_state import GlobalState
from states.task_state import TaskState
from states.step_state import StepState
from states.env_state import EnvState
from states.agent_state import AgentState
from models.model import Model

class MockModel(Model):
    def get_response(self, messages):
        return "Mock response"

def build_state(steps: int) -> GlobalState:
    # The last step mirrors live execution when a module runs: the environment
    # has been observed and the reasoner has set a thought, but no action yet.
    state = GlobalState()
    state.task_state = TaskState(
        task="Dice the carrot in the kitchen.",
        step_id=steps,
        max_steps=20,
        max_items=5,
        max_score=3)
    state.plan = "- [x] Find the kitchen\n- [ ] Dice the carrot"
    state.memories = {
        "kitchen": "rooms = {south = living room}",
        "knife": "location = kitchen"}
    for step_id in range(1, steps + 1):
        env_state = EnvState(
            feedback=f"Feedback for step {step_id}.",
            location=f"Room {step_id}",
            description=f"Description for step {step_id}.",
            inventory=f"Inventory for step {step_id}.",
            items=1,
            score=step_id)
        agent_state = AgentState(
            summary=f"action {step_id} → outcome {step_id}",
            memory=f"memory update {step_id}",
            thought=f"Thought for step {step_id}.",
            action=f"action {step_id}")
        step_state = StepState(step_id=step_id, env_state=env_state, agent_state=agent_state)
        state.step_history.append(step_state)
    state.step_history[-1].agent_state.action = ""
    return state
