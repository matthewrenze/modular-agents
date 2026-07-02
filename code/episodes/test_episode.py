import pytest
from episodes.episode import Episode
from results.results_manager import ResultsManager
from evals.eval_factory import EvalFactory


class TestEpisode:

    def test_skips_when_episode_exists(self, monkeypatch):
        monkeypatch.setattr(ResultsManager, "exists", lambda self, params: True)
        # If skipping works, the eval is never constructed.
        def fail(*args, **kwargs):
            raise AssertionError("should not construct eval when skipping")
        monkeypatch.setattr(EvalFactory, "create", fail)
        status = Episode().run("train", "gpt-5.4", "modular-full", "textworld", "tw-simple-1", 1)
        assert status == "skipped"

    def test_invalid_agent_raises(self):
        with pytest.raises(ValueError):
            Episode().run("train", "gpt-5.4", "bogus-agent", "textworld", "tw-simple-1", 1)

    def test_invalid_split_raises(self):
        with pytest.raises(ValueError):
            Episode().run("bogus-split", "gpt-5.4", "modular-full", "textworld", "tw-simple-1", 1)
