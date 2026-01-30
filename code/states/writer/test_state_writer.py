import io
import yaml
from states.task_state import TaskState
from states.writer import state_writer
from states.writer.state_writer import StateWriter
from common.parameters import Parameters
from states.global_state import GlobalState
from states.step_state import StepState
from states.env_state import EnvState
from states.agent_state import AgentState

TEST_YAML = """
task_state:
  task: Perform task 1.
  step_id: 3
  max_steps: 99
  max_items: 1
  max_score: 2
  max_reward: 1.0
  success: false
step_history:
  - step_id: 1
    env_state:
      feedback: ""
      location: Room 1
      description: You are in room 1.
      inventory: "You are carrying: item 1"
      items: 1
      score: 1
      reward: 0.50
      is_done: False
    agent_state:
      thought: I should do action 1.
      action: do action 1
      summary: Took action 1 in room 1.
  - step_id: 2
    env_state:
      feedback: You are now in room 2.
      location: Room 2
      description: You are in room 2.
      inventory: "You are carrying: item 1 and item 2"
      items: 2
      score: 2
      reward: 1.0
      is_done: True
    agent_state:
      thought: I should do action 2.
      action: do action 2
      summary: Took action 2 in room 2.
  - step_id: 3
    env_state:
      feedback: ""
      location: ""
      description: ""
      inventory: ""
      items: 0
      score: 0
      reward: 0.0
      is_done: False
    agent_state:
      thought: ""
      action: ""
      summary: ""
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
            task_state=TaskState(
                task="Perform task 1.",
                step_id=3,
                max_steps=99,
                max_items=1,
                max_score=2,
                max_reward=1.0),
            step_history=[
                StepState(
                    step_id=1,
                    env_state=EnvState(
                        location="Room 1",
                        description="You are in room 1.",
                        inventory="You are carrying: item 1",
                        items=1,
                        score=1,
                        reward=0.50,
                        is_done=False,
                    ),
                    agent_state=AgentState(
                        thought="I should do action 1.",
                        action="do action 1",
                        summary="Took action 1 in room 1.",
                    ),
                ),
                StepState(
                    step_id=2,
                    env_state=EnvState(
                        feedback="You are now in room 2.",
                        location="Room 2",
                        description="You are in room 2.",
                        inventory="You are carrying: item 1 and item 2",
                        items=2,
                        score=2,
                        reward=1.0,
                        is_done=True,
                    ),
                    agent_state=AgentState(
                        thought="I should do action 2.",
                        action="do action 2",
                        summary="Took action 2 in room 2.",
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

        expected_data = yaml.safe_load(TEST_YAML)
        actual_data = yaml.safe_load(captured["yaml_text"])
        assert expected_data == actual_data

class _CaptureWriter(io.StringIO):
    def __init__(self, on_close):
        super().__init__()
        self._on_close = on_close

    def close(self):
        self._on_close(self.getvalue())
        super().close()
