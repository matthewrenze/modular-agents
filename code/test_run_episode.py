import pytest
import run_episode
from run_episode import build_parser, run_episode as run_episode_fn
from results.results_manager import ResultsManager
from evals.eval_factory import EvalFactory


class TestRunEpisode:

    def test_parser_defaults_match_smoke_config(self):
        args = build_parser().parse_args([])
        assert args.split == "train"
        assert args.model == "gpt-5.4"
        assert args.agent == "modular-full"
        assert args.eval == "tw-simple-1"
        assert args.env == "textworld"
        assert args.episode == 1
        assert args.force is False

    def test_skips_when_episode_exists(self, monkeypatch):
        monkeypatch.setattr(ResultsManager, "exists", lambda self, params: True)
        # If skipping works, the eval is never constructed.
        def fail(*args, **kwargs):
            raise AssertionError("should not construct eval when skipping")
        monkeypatch.setattr(EvalFactory, "create", fail)
        status = run_episode_fn("train", "gpt-5.4", "modular-full", "textworld", "tw-simple-1", 1)
        assert status == "skipped"

    def test_invalid_agent_raises(self):
        with pytest.raises(ValueError):
            run_episode_fn("train", "gpt-5.4", "bogus-agent", "textworld", "tw-simple-1", 1)

    def test_invalid_split_raises(self):
        with pytest.raises(ValueError):
            run_episode_fn("bogus-split", "gpt-5.4", "modular-full", "textworld", "tw-simple-1", 1)
