import pytest
from common.parameters_factory import ParametersFactory
from common.parameters import Parameters

class TestParametersFactory:
    def test_create_reacter(self):
        factory = ParametersFactory()
        params = factory.create("react", "model", "env", "eval", 10)
        assert params.agent_name == "react"
        assert params.use_react
        assert not params.use_tasker
        assert not params.use_reasoner
        assert not params.use_actor

    def test_create_baseline(self):
        factory = ParametersFactory()
        params = factory.create("baseline", "model", "env", "eval", 10)
        assert params.agent_name == "baseline"
        assert not params.use_react
        assert not params.use_tasker
        assert not params.use_reasoner
        assert params.use_actor

    def test_create_topline(self):
        factory = ParametersFactory()
        params = factory.create("topline", "model", "env", "eval", 10)
        assert params.agent_name == "topline"
        assert not params.use_react
        assert params.use_tasker
        assert params.use_reasoner
        assert params.use_actor

    @pytest.mark.parametrize(
        "agent_name,true_param", [
        ("plus-tasker", "use_tasker"),
        ("plus-reasoner", "use_reasoner"),
    ])
    def test_create_with_plus(self, agent_name, true_param):
        factory = ParametersFactory()
        params = factory.create(agent_name, "model", "env", "eval", 10)
        assert params.agent_name == agent_name
        assert getattr(params, true_param)
        for attr in dir(params):
            if attr.startswith("use_") \
                    and attr != true_param:
                assert not getattr(params, attr)

    @pytest.mark.parametrize(
        "agent_name,false_param", [
        ("minus-tasker", "use_tasker"),
        ("minus-reasoner", "use_reasoner"),
    ])
    def test_create_with_minus(self, agent_name, false_param):
        factory = ParametersFactory()
        params = factory.create(agent_name, "model", "env", "eval", 10)
        assert params.agent_name == agent_name
        assert not getattr(params, false_param)
        for attr in dir(params):
            if attr.startswith("use_") \
                    and attr != false_param \
                    and attr != "use_react":
                assert getattr(params, attr)
