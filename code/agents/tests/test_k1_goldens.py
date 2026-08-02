import json
import pytest
from params.parameters_factory import ParametersFactory
from agents.agent_factory import AgentFactory
from agents.tests.golden_state import build_state, MockModel

# Golden files snapshot the exact prompts rendered by the pre-k-sweep code
# (captured 2026-08-01, v6.0 baselines). At k=1 every rendered prompt must
# stay byte-identical to these snapshots for both agent families.

GOLDENS = "agents/tests/goldens"
MODULES = ["summarizer", "memorizer", "planner", "reasoner", "actor"]

def create_agent(agent_name: str, subagent: str):
    params = ParametersFactory().create("test", "gpt-5.4", agent_name, "textworld", "tw-simple-1")
    params.max_steps = 20
    return AgentFactory().create(subagent, params, MockModel("mock"))

def read_golden(file_name: str) -> str:
    # Universal newlines, matching how the runtime reads templates: the
    # invariant is the in-memory prompt string, and this keeps the comparison
    # valid even if git's autocrlf rewrites the fixture files on checkout
    with open(f"{GOLDENS}/{file_name}") as file:
        return file.read()

class TestK1Goldens:

    @pytest.mark.parametrize("subagent", MODULES)
    def test_module_system_prompt_matches_golden(self, subagent):
        agent = create_agent("modular-full", subagent)
        assert agent.system_prompt == read_golden(f"{subagent}-system-k1.md")

    @pytest.mark.parametrize("steps", [1, 2, 12])
    @pytest.mark.parametrize("subagent", MODULES)
    def test_module_messages_match_golden(self, subagent, steps):
        agent = create_agent("modular-full", subagent)
        agent.execute(build_state(steps))
        assert agent.messages == json.loads(read_golden(f"{subagent}-messages-k1-steps-{steps}.json"))

    def test_react_k_system_prompt_matches_golden(self):
        agent = create_agent("react-k1", "react-k")
        assert agent.system_prompt == read_golden("react-k1-system-k1.md")

    @pytest.mark.parametrize("steps", [1, 2, 12])
    def test_react_k_messages_match_golden(self, steps):
        agent = create_agent("react-k1", "react-k")
        agent.execute(build_state(steps))
        assert agent.messages == json.loads(read_golden(f"react-k1-messages-k1-steps-{steps}.json"))
