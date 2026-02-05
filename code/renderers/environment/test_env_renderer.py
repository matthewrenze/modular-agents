from renderers.environment.env_renderer import EnvRenderer
from states.env_state import EnvState
from states.task_state import TaskState

class TestEnvRenderer:

    def test_render(self):
        env_state = EnvState(
            feedback="feedback 1",
            location="location 1",
            description="description 1",
            inventory="item 1",
            items=1,
            score=2,
            is_done=False)
        task_state = TaskState(
            task="task 1",
            max_steps=3,
            max_items=4,
            max_score=5)
        expected = (
            "Environment:\n"
            "  Feedback: feedback 1\n"
            "  Location: location 1\n"
            "  Description: description 1\n"
            "  Inventory: item 1\n"
            "  Capacity: 1 of 4 items\n"
            "  Score: 2 of 5\n"
            "  Done: False\n")

        renderer = EnvRenderer()
        actual = renderer.render(env_state, task_state)

        assert actual == expected

    def test_render_empty_feedback(self):
        env_state = EnvState(
            feedback="")
        task_state = TaskState()
        expected = (
            "Environment:\n"
            "  Location: \n"
            "  Description: \n"
            "  Inventory: \n"
            "  Capacity: 0 of 0 items\n"
            "  Score: 0 of 0\n"
            "  Done: False\n")

        renderer = EnvRenderer()
        actual = renderer.render(env_state, task_state)

        assert actual == expected

