import pytest
from params.parameters_factory import ParametersFactory

class TestParametersFactory:
    def test_create(self):
        factory = ParametersFactory()
        params = factory.create( "test", "model", "react-kn", "env", "eval",10)
        assert params.split_name == "test"
        assert params.model_name == "model"
        assert params.agent_name == "react-kn"
        assert params.env_name == "env"
        assert params.eval_name == "eval"
        assert params.eval_size == 10

    def test_create_defaults_eval_size(self):
        factory = ParametersFactory()
        params = factory.create("test", "model", "react-kn", "env", "eval")
        assert params.eval_size == 0

    def test_create_sets_episode_id(self):
        factory = ParametersFactory()
        params = factory.create("test", "model", "react-kn", "env", "eval", episode_id=5)
        assert params.episode_id == 5

    @pytest.mark.parametrize(
        "agent_name,true_param", [
        ("react-k0", "use_react_k0"),
        ("react-k1", "use_react_k1"),
        ("react-kn", "use_react_kn")])
    def test_create_react(self, agent_name, true_param):
        factory = ParametersFactory()
        params = factory.create( "test", "model", agent_name, "env", "eval",10)
        assert params.agent_name == agent_name
        assert getattr(params, true_param)
        for attr in dir(params):
            if attr.startswith("use_") and attr != true_param:
                assert not getattr(params, attr)

    def test_create_baseline(self):
        factory = ParametersFactory()
        params = factory.create("test","model", "modular-base",  "env", "eval", 10)
        assert params.agent_name == "modular-base"
        assert params.use_actor
        for attr in dir(params):
            if attr.startswith("use_") \
                    and attr != "use_actor" \
                    and attr != "use_reasoner":
                assert not getattr(params, attr)

    def test_create_topline(self):
        factory = ParametersFactory()
        params = factory.create("test","model", "modular-full",  "env", "eval", 10)
        assert params.agent_name == "modular-full"
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
        ("plus-summarizer", "use_summarizer"),
        ("plus-planner", "use_planner"),
        ("plus-memorizer", "use_memorizer"),
    ])
    def test_create_with_plus(self, agent_name, true_param):
        factory = ParametersFactory()
        params = factory.create("test","model", agent_name, "env", "eval", 10)
        assert params.agent_name == agent_name
        assert getattr(params, true_param)
        for attr in dir(params):
            if attr.startswith("use_") \
                    and attr != "use_actor" \
                    and attr != "use_reasoner" \
                    and attr != true_param:
                assert not getattr(params, attr)

    @pytest.mark.parametrize(
        "agent_name,false_param", [
        ("minus-summarizer", "use_summarizer"),
        ("minus-planner", "use_planner"),
        ("minus-memorizer", "use_memorizer"),
    ])
    def test_create_with_minus(self, agent_name, false_param):
        factory = ParametersFactory()
        params = factory.create("test","model", agent_name, "env", "eval", 10)
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

    @pytest.mark.parametrize(
        "agent_name", ["plus-planer", "minus-planer", "plus-foo", "minus-foo"])
    def test_create_rejects_unknown_module(self, agent_name):
        factory = ParametersFactory()
        with pytest.raises(ValueError):
            factory.create("test", "model", agent_name, "env", "eval", 10)
