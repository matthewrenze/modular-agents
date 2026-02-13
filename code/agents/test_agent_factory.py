import pytest
from params.parameters import Parameters
from models.model import Model
from agents.agent_factory import AgentFactory
from agents.react_k0.react_k0 import ReactK0
from agents.react_k1.react_k1 import ReactK1
from agents.react_kn.react_kn import ReactKn
from agents.tasker.tasker import Tasker
from agents.summarizer.summarizer import Summarizer
from agents.planner.planner import Planner
from agents.memorizer.memorizer import Memorizer
from agents.reasoner.reasoner import Reasoner
from agents.reviewer.reviewer import Reviewer
from agents.analyzer.analyzer import Analyzer
from agents.actor.actor import Actor


class TestAgentFactory:
    @pytest.mark.parametrize(
        "subagent,expected_class,expected_message",
        [("react-k0", ReactK0, "You are an intelligent agent that completes multi-step tasks."),
         ("react-k1", ReactK1, "You are an intelligent agent that completes multi-step tasks."),
         ("react-kn", ReactKn, "You are an intelligent agent that completes multi-step tasks."),
         ("tasker", Tasker, "You are the Tasker (task reviser) agent"),
         ("summarizer", Summarizer, "You are the Summarizer agent"),
         ("planner", Planner, "You are the Planner (plan creator and updater)"),
         ("memorizer", Memorizer, "You are the Memorizer (short-term memory) agent"),
         ("reasoner", Reasoner, "You are the Reasoner (chain-of-thought) agent"),
         ("actor", Actor, "You are the Actor (action selector) agent"),
         ("reviewer", Reviewer, "You are the Reviewer agent"),
         ("analyzer", Analyzer, "You are the Analyzer (review analyzer) agent")])
    def test_create_with_subagent(self, subagent, expected_class, expected_message):
        model = MockModel("")
        params = Parameters()
        factory = AgentFactory()
        agent = factory.create(subagent, params, model)
        assert isinstance(agent, expected_class)
        assert expected_message in agent.system_prompt
        assert "{system}" not in agent.system_prompt
        assert "{process}" not in agent.system_prompt
        assert "{actions}" not in agent.system_prompt
        assert "{max_steps}" not in agent.system_prompt
        assert "{examples}" not in agent.system_prompt

class MockModel(Model):
    def get_response(self, messages):
        return "Mock response"

