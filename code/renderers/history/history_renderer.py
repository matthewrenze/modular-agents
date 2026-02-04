from states.step_state import StepState

class HistoryRenderer:
    def render(self, step_history: list[StepState]) -> str:

        if len(step_history) == 0:
            return "History: N/A\n"

        output = "History:\n"
        for step in step_history:
            output += f"  Step {step.step_id}: {step.agent_state.summary}\n"

        return output