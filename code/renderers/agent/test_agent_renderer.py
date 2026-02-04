from renderers.agent.agent_renderer import AgentRenderer
from states.agent_state import AgentState

class TestAgentRenderer:

    def test_render(self):
        agent_state = AgentState(
            summary="summary 1",
            memory="memory 1",
            thought="thought 1",
            action="action 1")

        renderer = AgentRenderer()
        rendered_output = renderer.render(agent_state)

        expected_output = (
            "Agent:\n"
            "  Summary: summary 1\n"
            "  Memory:\n memory 1\n"
            "  Thought: thought 1\n"
            "  Action: action 1\n")

        assert rendered_output == expected_output

    def test_render_empty(self):

        agent_state = AgentState(
            summary="",
            memory="",
            thought="",
            action=""
        )

        renderer = AgentRenderer()
        rendered_output = renderer.render(agent_state)

        expected_output = "Agent:\n"

        assert rendered_output == expected_output