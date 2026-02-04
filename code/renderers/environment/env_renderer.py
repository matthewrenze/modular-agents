from states.env_state import EnvState
from states.task_state import TaskState

class EnvRenderer:
    def render(self, env_state: EnvState, task_state: TaskState) -> str:

        result = f"Environment:\n" \

        if env_state.feedback != "":
            result += f"  Feedback: {env_state.feedback}\n" \

        result += f"  Location: {env_state.location}\n" \
            + f"  Description: {env_state.description}\n" \
            + f"  Inventory: {env_state.inventory}\n" \
            + f"  Capacity: {env_state.items} of {task_state.max_items} items\n" \
            + f"  Score: {env_state.score} of {task_state.max_score}\n" \
            + f"  Done: {env_state.is_done}\n"

        return result