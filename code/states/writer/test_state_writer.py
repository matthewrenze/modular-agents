import io
import yaml

from plans.plan_step import PlanStep
from states.task_state import TaskState
from states.writer import state_writer
from states.writer.state_writer import StateWriter
from params.parameters import Parameters
from states.global_state import GlobalState
from states.step_state import StepState
from states.env_state import EnvState
from states.agent_state import AgentState

class TestStateWriter:
    def test_write(self, monkeypatch):
        params = Parameters(
            model_name="model",
            agent_name="agent",
            eval_name="eval")
        episode_id = 123
        state = GlobalState(
            task_state=TaskState(
                task="task 1",
                step_id=3,
                max_steps=99,
                max_items=1,
                max_score=2,
                max_reward=1.0),
            plan=[
                PlanStep(id=1, status="done", label="step 1"),
                PlanStep(id=2, status="todo", label="step 2")],
            memories={
                1: "memory 1",
                2: "memory 2",},
            step_history=[
                StepState(
                    step_id=1,
                    env_state=EnvState(
                        location="location 1",
                        description="description 1",
                        inventory="inventory 1",
                        items=1,
                        score=1,
                        reward=0.50,
                        is_done=False,
                    ),
                    agent_state=AgentState(
                        summary="summary 1",
                        plan="add: plan 1\ninsert: 2 = plan 2\nupdate: 3 = plan 3\n",
                        memory="create: memory 1\ndelete: 1\n",
                        thought="thought 1",
                        action="action 1",
                    ),
                ),
                StepState(
                    step_id=2,
                    env_state=EnvState(
                        feedback="feedback 2",
                        location="location 2",
                        description="description 2",
                        inventory="inventory 2",
                        items=2,
                        score=2,
                        reward=1.0,
                        is_done=True,
                    ),
                    agent_state=AgentState(
                        summary="summary 2",
                        plan="mark: 4\ndelete: 5\ndelete: 6\n",
                        memory="create: memory 2\ncreate: memory 3\ndelete: 2\ndelete: 3\n",
                        thought="thought 2",
                        action="action 2",
                    ),
                ),
                StepState(
                    step_id=3,
                    env_state=EnvState(),      # defaults -> should dump as {}
                    agent_state=AgentState(),  # defaults -> should dump as {}
                ),
            ],
        )

        expected_folder = "../data/states/model - agent - eval"
        expected_file_path = f"{expected_folder}/{episode_id}.yaml"
        with open("states/test_file.yaml", "r", encoding="utf-8") as f:
            expected_yaml = f.read()

        # Capture calls + written YAML
        captured = {"makedirs": None, "open": None, "yaml_text": None}

        def fake_makedirs(path, exist_ok=False):
            captured["makedirs"] = (path, exist_ok)

        def fake_open(file_path, mode="r", encoding=None, *args, **kwargs):
            captured["open"] = (file_path, mode, encoding)
            assert file_path == expected_file_path
            assert mode == "w"
            assert encoding == "utf-8"

            return _CaptureWriter(lambda text: captured.__setitem__("yaml_text", text))

        monkeypatch.setattr(state_writer.os, "makedirs", fake_makedirs, raising=True)
        monkeypatch.setattr(state_writer, "open", fake_open, raising=False)

        writer = StateWriter()
        writer.write(state, params, episode_id)

        assert captured["makedirs"] == (expected_folder, True)
        assert captured["open"] == (expected_file_path, "w", "utf-8")

        expected = yaml.safe_load(expected_yaml)
        actual = yaml.safe_load(captured["yaml_text"])
        assert expected == actual

class _CaptureWriter(io.StringIO):
    def __init__(self, on_close):
        super().__init__()
        self._on_close = on_close

    def close(self):
        self._on_close(self.getvalue())
        super().close()
