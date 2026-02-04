from states.step_state import StepState
from states.task_state import TaskState

class StepRenderer:
    def render(self, step_state: StepState, task_state: TaskState) -> str:
        output = f"Step: {step_state.step_id} of {task_state.max_steps}\n"
        return output