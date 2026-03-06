import pytest
from params.parameters_factory import ParametersFactory

class TestParametersFactory:
    @pytest.mark.parametrize(
        "agent_name,true_param", [
        ("react-k0", "use_react_k0"),
        ("react-k1", "use_react_k1"),
        ("react-kn", "use_react_kn")])
    def test_create_react(self, agent_name, true_param):
        factory = ParametersFactory()
        params = factory.create( "model", agent_name, "env", "eval",10)
        assert params.agent_name == agent_name
        assert getattr(params, true_param)
        for attr in dir(params):
            if attr.startswith("use_") and attr != true_param:
                assert not getattr(params, attr)

    def test_create_baseline(self):
        factory = ParametersFactory()
        params = factory.create("model", "baseline",  "env", "eval", 10)
        assert params.agent_name == "baseline"
        assert params.use_actor
        for attr in dir(params):
            if attr.startswith("use_") and attr != "use_actor":
                assert not getattr(params, attr)

    def test_create_topline(self):
        factory = ParametersFactory()
        params = factory.create("model", "topline",  "env", "eval", 10)
        assert params.agent_name == "topline"
        assert params.use_actor
        for attr in dir(params):
            if (attr.startswith("use_")
                    and attr != "use_tasker"
                    and attr != "use_actor"
                    and attr != "use_react_k0"
                    and attr != "use_react_k1"
                    and attr != "use_react_kn"):
                assert getattr(params, attr)

    @pytest.mark.parametrize(
        "agent_name,true_param", [
        # ("plus-tasker", "use_tasker"),
        ("plus-summarizer", "use_summarizer"),
        ("plus-planner", "use_planner"),
        ("plus-memorizer", "use_memorizer"),
        ("plus-reasoner", "use_reasoner"),
    ])
    def test_create_with_plus(self, agent_name, true_param):
        factory = ParametersFactory()
        params = factory.create("model", agent_name, "env", "eval", 10)
        assert params.agent_name == agent_name
        assert getattr(params, true_param)
        for attr in dir(params):
            if attr.startswith("use_") \
                    and attr != "use_actor" \
                    and attr != true_param:
                assert not getattr(params, attr)

    @pytest.mark.parametrize(
        "agent_name,false_param", [
        # ("minus-tasker", "use_tasker"),
        ("minus-summarizer", "use_summarizer"),
        ("minus-planner", "use_planner"),
        ("minus-memorizer", "use_memorizer"),
        ("minus-reasoner", "use_reasoner"),
    ])
    def test_create_with_minus(self, agent_name, false_param):
        factory = ParametersFactory()
        params = factory.create("model", agent_name, "env", "eval", 10)
        assert params.agent_name == agent_name
        assert not getattr(params, false_param)
        for attr in dir(params):
            if attr.startswith("use_") \
                    and attr != false_param \
                    and attr != "use_tasker" \
                    and attr != "use_react_k0" \
                    and attr != "use_react_k1" \
                    and attr != "use_react_kn":
                assert getattr(params, attr)
