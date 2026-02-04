from states.task_state import TaskState

class TaskRenderer:
    def render(self, task_state: TaskState) -> str:
        output = f"Task: {task_state.task}\n"
        return output