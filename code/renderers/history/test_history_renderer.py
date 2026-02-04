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

        renderer = HistoryRenderer()
        rendered_output = renderer.render(step_history)

        expected_output = (
            "History:\n"
            "  Step 1: summary 1\n"
            "  Step 2: summary 2\n")

        assert rendered_output == expected_output

    def test_render_empty(self):
        renderer = HistoryRenderer()
        rendered_output = renderer.render([])

        expected_output = "History: N/A\n"

        assert rendered_output == expected_output