from renderers.history.history_renderer import HistoryRenderer
from states.step_state import StepState
from states.env_state import EnvState
from states.agent_state import AgentState

class TestHistoryRenderer:

    def test_render(self):
        step_history = [
            StepState(
                step_id=1,
                env_state=EnvState(),
                agent_state=AgentState(
                    summary="summary 1")),
            StepState(
                step_id=2,
                env_state=EnvState(),
                agent_state=AgentState(
                    summary="summary 2"))]
        expected = (
            "History:\n"
            "  Step 1: summary 1\n"
            "  Step 2: summary 2\n")

        renderer = HistoryRenderer()
        actual = renderer.render(step_history)

        assert actual == expected

    def test_render_empty(self):
        expected = "History: N/A\n"

        renderer = HistoryRenderer()
        actual = renderer.render([])

        assert actual == expected