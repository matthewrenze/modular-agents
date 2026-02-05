from renderers.agent.agent_renderer import AgentRenderer
from states.agent_state import AgentState

class TestAgentRenderer:

    def test_render(self):
        agent_state = AgentState(
            summary="summary 1",
            plan="add: 1\ninsert: 2\nupdate: 3\nmark: 4\ndelete: 5",
            memory="delete: 1\ncreate: 2",
            thought="thought 1",
            action="action 1")
        expected = (
            "Agent:\n"
            "  Summary: summary 1\n"
            "  Plan:\n"
            "    add: 1\n"
            "    insert: 2\n"
            "    update: 3\n"
            "    mark: 4\n"
            "    delete: 5\n"
            "  Memory:\n"
            "    delete: 1\n"
            "    create: 2\n"
            "  Thought: thought 1\n"
            "  Action: action 1\n")

        renderer = AgentRenderer()
        actual = renderer.render(agent_state)

        assert actual == expected

    def test_render_empty(self):
        agent_state = AgentState(
            summary="",
            memory="",
            thought="",
            action="")
        expected = "Agent:\n"

        renderer = AgentRenderer()
        actual = renderer.render(agent_state)

        assert actual == expected