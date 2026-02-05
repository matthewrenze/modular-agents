from renderers.task.task_renderer import TaskRenderer
from states.task_state import TaskState

class TestTaskRenderer:
    def test_render_task(self):
        task_state = TaskState(task="task 1")
        expected = "Task: task 1\n"

        renderer = TaskRenderer()
        actual = renderer.render(task_state)

        assert actual == expected
