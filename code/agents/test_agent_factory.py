import pytest
from common.parameters import Parameters
from models.model import Model
from agents.agent_factory import AgentFactory
from agents.react.react_agent import ReactAgent
from agents.actor.actor_agent import ActorAgent
from agents.tasker.tasker_agent import TaskerAgent
from agents.reasoner.reasoner_agent import ReasonerAgent
from agents.summarizer.summarizer import Summarizer

class TestAgentFactory:
    @pytest.mark.parametrize(
        "subagent,expected_class,expected_message",
        [("react", ReactAgent, "You are an intelligent agent that completes multi-step tasks."),
         ("actor", ActorAgent, "You are the Actor (action selector) agent"),
         ("tasker", TaskerAgent, "You are the Tasker (task reviser) agent"),
         ("reasoner", ReasonerAgent, "You are the Reasoner (chain-of-thought) agent"),
         ("summarizer", Summarizer, "You are the Summarizer (state-action summary) agent "),])
    def test_create_with_subagent(self, subagent, expected_class, expected_message):
        model = MockModel()
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

