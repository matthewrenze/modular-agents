import io
import yaml
from states.writer import state_writer
from states.writer.state_writer import StateWriter
from common.parameters import Parameters
from states.global_state import GlobalState
from states.step_state import StepState
from states.env_state import EnvState
from states.agent_state import AgentState


TEST_YAML = """
task: Perform task 1.
current_step_id: 3
step_history:
  - step_id: 1
    env_state:
      location: Room 1
      description: You are in room 1.
      inventory: "You are carrying: item 1"
      score: 1
      max_score: 2
      reward: 0.50
      max_reward: 1.0
      is_done: false
    agent_state:
      thought: I should do action 1.
      action: do action 1
  - step_id: 2
    env_state:
      feedback: You are now in room 2.
      location: Room 2
      description: You are in room 2.
      inventory: "You are carrying: item 1 and item 2"
      score: 2
      max_score: 2
      reward: 1.0
      max_reward: 1.0
      is_done: true
    agent_state:
      thought: I should do action 2.
      action: do action 2
  - step_id: 3
    env_state: {}
    agent_state: {}
"""

class TestStateWriter:
    def test_write(self, monkeypatch):
        params = Parameters(
            agent_name="agent-a",
            model_name="model-b",
            eval_name="eval-c")
        episode_id = 123
        expected_folder = "../data/states/agent-a - model-b - eval-c"
        expected_file = f"{expected_folder}/{episode_id}.yaml"

        # Build a state equivalent to TEST_YAML
        state = GlobalState(
            task="Perform task 1.",
            current_step_id=3,
            step_history=[
                StepState(
                    step_id=1,
                    env_state=EnvState(
                        location="Room 1",
                        description="You are in room 1.",
                        inventory="You are carrying: item 1",
                        score=1,
                        max_score=2,
                        reward=0.50,
                        max_reward=1.0,
                        is_done=False,
                    ),
                    agent_state=AgentState(
                        thought="I should do action 1.",
                        action="do action 1",
                    ),
                ),
                StepState(
                    step_id=2,
                    env_state=EnvState(
                        feedback="You are now in room 2.",
                        location="Room 2",
                        description="You are in room 2.",
                        inventory="You are carrying: item 1 and item 2",
                        score=2,
                        max_score=2,
                        reward=1.0,
                        max_reward=1.0,
                        is_done=True,
                    ),
                    agent_state=AgentState(
                        thought="I should do action 2.",
                        action="do action 2",
                    ),
                ),
                StepState(
                    step_id=3,
                    env_state=EnvState(),      # defaults -> should dump as {}
                    agent_state=AgentState(),  # defaults -> should dump as {}
                ),
            ],
        )

        # Capture calls + written YAML
        captured = {"makedirs": None, "open": None, "yaml_text": None}

        def fake_makedirs(path, exist_ok=False):
            captured["makedirs"] = (path, exist_ok)

        def fake_open(file_path, mode="r", encoding=None, *args, **kwargs):
            captured["open"] = (file_path, mode, encoding)
            assert file_path == expected_file
            assert mode == "w"
            assert encoding == "utf-8"

            return _CaptureWriter(lambda text: captured.__setitem__("yaml_text", text))

        monkeypatch.setattr(state_writer.os, "makedirs", fake_makedirs, raising=True)
        monkeypatch.setattr(state_writer, "open", fake_open, raising=False)

        writer = StateWriter()
        writer.write(state, params, episode_id)

        assert captured["makedirs"] == (expected_folder, True)
        assert captured["open"] == (expected_file, "w", "utf-8")

        data = yaml.safe_load(captured["yaml_text"])

        # Verify top-level
        assert data["task"] == "Perform task 1."
        assert data["current_step_id"] == 3
        assert len(data["step_history"]) == 3

        # Verify step 1
        s1 = data["step_history"][0]
        assert s1["step_id"] == 1
        e1 = s1["env_state"]
        assert e1["feedback"] == ""
        assert e1["location"] == "Room 1"
        assert e1["description"] == "You are in room 1."
        assert e1["inventory"] == "You are carrying: item 1"
        assert e1["score"] == 1
        assert e1["max_score"] == 2
        assert e1["reward"] == 0.5
        assert e1["max_reward"] == 1.0
        assert e1["is_done"] is False
        a1 = s1["agent_state"]
        assert a1["thought"] == "I should do action 1."
        assert a1["action"] == "do action 1"

        # Verify step 2
        s2 = data["step_history"][1]
        assert s2["step_id"] == 2
        e2 = s2["env_state"]
        assert e2["feedback"] == "You are now in room 2."
        assert e2["location"] == "Room 2"
        assert e2["description"] == "You are in room 2."
        assert e2["inventory"] == "You are carrying: item 1 and item 2"
        assert e2["score"] == 2
        assert e2["max_score"] == 2
        assert e2["reward"] == 1.0
        assert e2["max_reward"] == 1.0
        assert e2["is_done"] is True
        a2 = s2["agent_state"]
        assert a2["thought"] == "I should do action 2."
        assert a2["action"] == "do action 2"

        # Verify step 3 (defaults)
        s3 = data["step_history"][2]
        assert s3["step_id"] == 3
        e3 = s3["env_state"]
        assert e3["feedback"] == ""
        assert e3["location"] == ""
        assert e3["description"] == ""
        assert e3["inventory"] == ""
        assert e3["score"] == 0
        assert e3["max_score"] == 0
        assert e3["reward"] == 0.0
        assert e3["max_reward"] == 1.0
        assert e3["is_done"] is False
        a3 = s3["agent_state"]
        assert a3["thought"] == ""
        assert a3["action"] == ""

class _CaptureWriter(io.StringIO):
    def __init__(self, on_close):
        super().__init__()
        self._on_close = on_close

    def close(self):
        self._on_close(self.getvalue())
        super().close()
