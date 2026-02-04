from renderers.task.task_renderer import TaskRenderer
from states.task_state import TaskState

class TestTaskRenderer:
    def test_render_task(self):
        task_state = TaskState(task="task 1")

        renderer = TaskRenderer()
        rendered_output = renderer.render(task_state)

        expected_output = "Task: task 1\n"

        assert rendered_output == expected_output
