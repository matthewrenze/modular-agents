import sys
import pytest
from params.parameters_factory import ParametersFactory
from agents.agent_factory import AgentFactory
from agents.tests.golden_state import build_state, MockModel

def create_agent(subagent: str, agent_name: str):
    params = ParametersFactory().create("test", "gpt-5.4", agent_name, "textworld", "tw-simple-1")
    params.max_steps = 20
    return AgentFactory().create(subagent, params, MockModel("mock"))

class TestReactK:

    @pytest.mark.parametrize("steps", [1, 2, 12])
    def test_k1_matches_react_k1_oracle(self, steps):
        react_k = create_agent("react-k", "react-k1")
        react_k1 = create_agent("react-k1", "react-k1")
        react_k.execute(build_state(steps))
        react_k1.execute(build_state(steps))
        assert react_k.system_prompt == react_k1.system_prompt
        assert react_k.messages == react_k1.messages

    def test_k5_window(self):
        react_k = create_agent("react-k", "react-k5")
        react_k.execute(build_state(12))
        # system + task + 5 previous (user, assistant) pairs + current + response
        assert len(react_k.messages) == 14
        assert "Step: 7 of 20" in react_k.messages[2]["content"]
        assert "Step: 12 of 20" in react_k.messages[12]["content"]
        all_content = "".join(message["content"] for message in react_k.messages)
        assert "Step: 6 of 20" not in all_content
        assert "the previous 5 steps and the current step" in react_k.system_prompt

    def test_kn_window(self):
        react_k = create_agent("react-k", "react-k5")
        react_k.params.k = sys.maxsize
        react_k.execute(build_state(12))
        # system + task + 11 previous (user, assistant) pairs + current + response
        assert len(react_k.messages) == 26
        assert "Step: 1 of 20" in react_k.messages[2]["content"]
        assert "Step: 12 of 20" in react_k.messages[24]["content"]

    def test_k1_window_on_first_step(self):
        react_k = create_agent("react-k", "react-k1")
        react_k.execute(build_state(1))
        # system + task + current + response: no previous-step messages
        assert len(react_k.messages) == 4
