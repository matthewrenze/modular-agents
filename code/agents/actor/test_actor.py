import pytest
from params.parameters import Parameters
from models.gpt_model import GptModel
from states.reader.state_reader import StateReader
from agents.agent_factory import AgentFactory

class TestActor:

    @pytest.mark.agent
    def test_execute(self):
        agent_factory = AgentFactory()
        params = Parameters()
        model = GptModel("gpt-5.2")
        state_reader = StateReader()
        state = state_reader.read("agents/actor/tests/test.yaml")
        agent = agent_factory.create("actor", params, model)
        response = agent.execute(state)
        assert response == "dice carrot with knife"