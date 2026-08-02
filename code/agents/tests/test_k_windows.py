import pytest
from params.parameters_factory import ParametersFactory
from agents.agent_factory import AgentFactory
from agents.tests.golden_state import build_state, MockModel

MODULES = ["summarizer", "memorizer", "planner", "reasoner", "actor"]

def create_agent(subagent: str, agent_name: str):
    params = ParametersFactory().create("test", "gpt-5.4", agent_name, "textworld", "tw-simple-1")
    params.max_steps = 20
    return AgentFactory().create(subagent, params, MockModel("mock"))

def user_content(subagent: str, agent_name: str, steps: int = 12) -> str:
    agent = create_agent(subagent, agent_name)
    agent.execute(build_state(steps))
    return agent.messages[1]["content"]

class TestKWindows:

    @pytest.mark.parametrize("subagent", MODULES)
    def test_k5_includes_five_previous_steps(self, subagent):
        content = user_content(subagent, "modular-k5")
        for step_id in range(7, 13):
            assert f"Step: {step_id} of 20" in content
        assert "Step: 6 of 20" not in content

    @pytest.mark.parametrize("subagent", MODULES)
    def test_k5_previous_steps_stay_ordered(self, subagent):
        content = user_content(subagent, "modular-k5")
        positions = [content.index(f"Step: {step_id} of 20") for step_id in range(7, 13)]
        assert positions == sorted(positions)

    @pytest.mark.parametrize("subagent", MODULES)
    def test_kn_includes_all_previous_steps(self, subagent):
        content = user_content(subagent, "modular-kn")
        for step_id in range(1, 13):
            assert f"Step: {step_id} of 20" in content

    @pytest.mark.parametrize("subagent", MODULES)
    def test_k5_clamps_to_available_steps(self, subagent):
        content = user_content(subagent, "modular-k5", steps=3)
        for step_id in range(1, 4):
            assert f"Step: {step_id} of 20" in content

    @pytest.mark.parametrize("subagent", ["summarizer", "memorizer"])
    def test_summarizer_memorizer_k5_previous_steps_have_no_env(self, subagent):
        content = user_content(subagent, "modular-k5")
        assert "Feedback for step 11." not in content
        assert "Feedback for step 12." in content
        assert "Action: action 11" in content

    def test_memorizer_k5_previous_steps_follow_memories(self):
        content = user_content("memorizer", "modular-k5")
        assert content.index("Memories:") < content.index("Step: 7 of 20")

    def test_planner_k5_previous_steps_have_env_and_follow_plan(self):
        content = user_content("planner", "modular-k5")
        assert "Feedback for step 7." in content
        assert "Action: action 7" in content
        assert "Feedback for step 6." not in content
        assert content.index("Plan:") < content.index("Step: 7 of 20")

    def test_reasoner_k5_current_step_has_no_agent_state(self):
        content = user_content("reasoner", "modular-k5")
        assert "Feedback for step 7." in content
        assert "Thought: Thought for step 11." in content
        assert "Thought: Thought for step 12." not in content

    def test_actor_k5_current_step_has_thought(self):
        content = user_content("actor", "modular-k5")
        assert "Feedback for step 7." in content
        assert "Thought: Thought for step 12." in content

    @pytest.mark.parametrize("subagent", MODULES)
    def test_k5_system_prompt_states_widened_window(self, subagent):
        agent = create_agent(subagent, "modular-k5")
        assert "the previous 5 steps and the current step" in agent.system_prompt
        assert "the previous step and the current step" not in agent.system_prompt

    @pytest.mark.parametrize("subagent", MODULES)
    def test_kn_system_prompt_states_full_window(self, subagent):
        agent = create_agent(subagent, "modular-kn")
        assert "all previous steps and the current step" in agent.system_prompt
