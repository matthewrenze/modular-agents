import pandas as pd
import pytest
import artifacts.artifacts
import episodes.episode
from episodes.episode import Episode
from logs.log_factory import LogFactory
from models.model import Model
from results.results_manager import ResultsManager
from evals.eval_factory import EvalFactory
from environments.env_factory import EnvFactory
from models.model_factory import ModelFactory
from agents.agent_factory import AgentFactory
from details.details_manager import DetailsManager
from messages.messages_writer import MessagesWriter
from states.writer.state_writer import StateWriter
from states.env_state import EnvState
from states.task_state import TaskState


class FakeEnv:
    """Scripted environment: not done until `done_after` steps, then done with `reward`.
    Never done if `done_after` is None (the loop's max-steps backstop must end the episode)."""

    def __init__(self, done_after=None, reward=0.0):
        self.done_after = done_after
        self.reward = reward
        self.steps = 0

    def reset(self, episode_id):
        return TaskState(task="test task", max_score=1), self._state()

    def step(self, action):
        self.steps += 1
        return self._state()

    def _state(self):
        is_done = self.done_after is not None and self.steps >= self.done_after
        reward = self.reward if is_done else 0.0
        return EnvState(is_done=is_done, reward=reward, score=int(reward))


class StubAgent:

    def __init__(self):
        self.messages = []

    def reset(self):
        pass

    def execute(self, global_state):
        return "a thought", "an action"


class RaisingAgent(StubAgent):

    def execute(self, global_state):
        raise RuntimeError("agent exploded")


class StubLog:

    def __init__(self, *args):
        pass

    def __getattr__(self, name):
        return lambda *args, **kwargs: None


@pytest.fixture
def run_episode(monkeypatch):
    """Runs Episode.run with a scripted env, stub agents/model, and all file writers disabled.
    solution_steps=2 clamps max_steps to steps_floor (20). Returns (status, saved result row)."""

    def _run(env, agent=None, force=False):
        agent = agent or StubAgent()
        saved = {}
        monkeypatch.setattr(episodes.episode, "sleep_time", 0)
        monkeypatch.setattr(LogFactory, "create", lambda self, renderer, artifacts, params: StubLog())
        monkeypatch.setattr(ResultsManager, "exists", lambda self, params: False)
        monkeypatch.setattr(ResultsManager, "save", lambda self, params, row: saved.update(row=row))
        monkeypatch.setattr(EvalFactory, "create", lambda self, params: pd.DataFrame([{"solution_steps": 2}]))
        monkeypatch.setattr(EnvFactory, "create", lambda self, params, eval: env)
        monkeypatch.setattr(ModelFactory, "create", lambda self, params, use_azure: Model("stub-model"))
        monkeypatch.setattr(AgentFactory, "create", lambda self, name, params, model: agent)
        monkeypatch.setattr(DetailsManager, "save", lambda self: None)
        monkeypatch.setattr(MessagesWriter, "write", lambda self, *args: None)
        monkeypatch.setattr(StateWriter, "write", lambda self, *args: None)
        status = Episode().run("train", "gpt-5.4", "react-k0", "textworld", "tw-simple-1", 1, force=force)
        return status, saved["row"]

    return _run


class TestEpisode:

    def test_success(self, run_episode):
        status, row = run_episode(FakeEnv(done_after=3, reward=1.0))
        assert status == "success"
        assert row.success is True
        assert row.reward == 1.0
        assert row.steps == 3
        assert row.max_steps_hit is False

    def test_failure(self, run_episode):
        status, row = run_episode(FakeEnv(done_after=3, reward=0.5))
        assert status == "failure"
        assert row.success is False
        assert row.reward == 0.5
        assert row.max_steps_hit is False

    def test_timeout_env_done_at_max_steps(self, run_episode):
        status, row = run_episode(FakeEnv(done_after=20, reward=0.0))
        assert status == "failure"
        assert row.steps == 20
        assert row.max_steps_hit is True

    def test_timeout_env_never_done(self, run_episode):
        status, row = run_episode(FakeEnv())
        assert status == "failure"
        assert row.steps == 20
        assert row.max_steps_hit is True

    def test_win_at_max_steps(self, run_episode):
        status, row = run_episode(FakeEnv(done_after=20, reward=1.0))
        assert status == "success"
        assert row.max_steps_hit is False

    def test_error(self, run_episode):
        status, row = run_episode(FakeEnv(), agent=RaisingAgent())
        assert status == "error"
        assert "RuntimeError: agent exploded" in row.error
        assert row.max_steps_hit is False

    def test_skips_when_episode_exists(self, monkeypatch):
        monkeypatch.setattr(ResultsManager, "exists", lambda self, params: True)
        # If skipping works, the eval is never constructed.
        def fail(*args, **kwargs):
            raise AssertionError("should not construct eval when skipping")
        monkeypatch.setattr(EvalFactory, "create", fail)
        status = Episode().run("train", "gpt-5.4", "modular-full", "textworld", "tw-simple-1", 1)
        assert status == "skipped"

    def test_force_retries_rmtree_on_permission_error(self, run_episode, monkeypatch):
        rmtree_calls = []
        sleeps = []

        def flaky_rmtree(path):
            rmtree_calls.append(path)
            if len(rmtree_calls) < 3:
                raise PermissionError("locked by Dropbox")

        monkeypatch.setattr(artifacts.artifacts.os.path, "exists", lambda path: True)
        monkeypatch.setattr(artifacts.artifacts.shutil, "rmtree", flaky_rmtree)
        monkeypatch.setattr(artifacts.artifacts.time, "sleep", lambda seconds: sleeps.append(seconds))
        status, row = run_episode(FakeEnv(done_after=3, reward=1.0), force=True)
        assert status == "success"
        assert len(rmtree_calls) == 3
        assert sleeps[:2] == [1, 2]

    def test_force_reraises_rmtree_permission_error_after_five_attempts(self, monkeypatch):
        rmtree_calls = []

        def locked_rmtree(path):
            rmtree_calls.append(path)
            raise PermissionError("locked by Dropbox")

        monkeypatch.setattr(artifacts.artifacts.os.path, "exists", lambda path: True)
        monkeypatch.setattr(artifacts.artifacts.shutil, "rmtree", locked_rmtree)
        monkeypatch.setattr(artifacts.artifacts.time, "sleep", lambda seconds: None)
        with pytest.raises(PermissionError):
            Episode().run("train", "gpt-5.4", "react-k0", "textworld", "tw-simple-1", 1, force=True)
        assert len(rmtree_calls) == 5

    def test_invalid_agent_raises(self):
        with pytest.raises(ValueError):
            Episode().run("train", "gpt-5.4", "bogus-agent", "textworld", "tw-simple-1", 1)

    def test_invalid_split_raises(self):
        with pytest.raises(ValueError):
            Episode().run("bogus-split", "gpt-5.4", "modular-full", "textworld", "tw-simple-1", 1)
