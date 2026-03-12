from renderers.agent.agent_renderer import AgentRenderer
from states.agent_state import AgentState

class TestAgentRenderer:

    def test_render(self):
        agent_state = AgentState(
            summary="summary 1",
            plan="- [x] Step 1\n- [ ] Step 2",
            memory="delete: 1\nupdate: 2 = memory 2\ncreate: memory 3",
            thought="thought 1",
            action="action 1")
        expected = (
            "Agent:\n"
            "  Thought: thought 1\n"
            "  Action: action 1\n")

        renderer = AgentRenderer()
        actual = renderer.render(agent_state)

        assert actual == expected

    def test_render_log_mode(self):
        agent_state = AgentState(
            summary="summary 1",
            plan="- [x] step 1\n- [ ] step 2",
            memory="item 1: value 1\nitem 2: value 2\nitem 3: value 3",
            thought="thought 1",
            action="action 1")
        expected = (
            "Agent:\n"
            "  Summary: summary 1\n"
            "  Memory:\n"
            "    item 1: value 1\n"
            "    item 2: value 2\n"
            "    item 3: value 3\n"
            "  Plan:\n"
            "    - [x] step 1\n"
            "    - [ ] step 2\n"
            "  Thought: thought 1\n"
            "  Action: action 1\n")

        renderer = AgentRenderer()
        actual = renderer.render(agent_state, True)

        assert actual == expected

    def test_render_empty(self):
        agent_state = AgentState(
            summary="",
            plan="",
            memory="",
            thought="",
            action="")
        expected = "Agent:\n"

        renderer = AgentRenderer()
        actual = renderer.render(agent_state, True)

        assert actual == expected
