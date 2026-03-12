import io
from states.reader import state_reader
from states.reader.state_reader import StateReader

class TestStateReader:
    def test_read(self, monkeypatch):

        with open("states/test_file.yaml", "r", encoding="utf-8") as f:
            input_yaml = f.read()

        # Create a fake open function to mock file reading
        def fake_open(file_path, mode="r", encoding=None, *args, **kwargs):
            assert file_path == "states/reader/test_state.yaml"
            assert mode == "r"
            assert encoding == "utf-8"
            return io.StringIO(input_yaml)

        monkeypatch.setattr(state_reader, "open", fake_open, raising=False)

        # Create the state reader
        reader = StateReader()
        state = reader.read("states/reader/test_state.yaml")

        # Verify task state
        t1 = state.task_state
        assert t1.task == "task 1"
        assert t1.step_id == 3
        assert t1.max_steps == 99
        assert t1.max_items == 1
        assert t1.max_score == 2
        assert t1.max_reward == 1.0
        assert t1.success is False

        # Verify plan
        assert state.plan == "- [x] step 1\n- [ ] step 2\n"

        # Verify memories
        assert len(state.memories) == 2
        assert state.memories["key 1"] == "value 1"
        assert state.memories["key 2"] == "value 2"

        # Verify step history
        assert len(state.step_history) == 2

        # Verify the first step
        s1 = state.step_history[0]
        assert s1.step_id == 1
        assert s1.env_state.feedback == ""
        assert s1.env_state.location == "location 1"
        assert s1.env_state.description == "description 1"
        assert s1.env_state.inventory == "inventory 1"
        assert s1.env_state.items == 1
        assert s1.env_state.score == 1
        assert s1.env_state.reward == 0.50
        assert s1.env_state.is_done is False
        assert s1.agent_state.summary == "summary 1"
        assert s1.agent_state.plan == "- [x] step 1\n- [x] step 2\n"
        assert s1.agent_state.memory == "key 3: value 3\n"
        assert s1.agent_state.thought == "thought 1"
        assert s1.agent_state.action == "action 1"

        # Verify the defaults (second step)
        s3 = state.step_history[1]
        assert s3.step_id == 2
        assert s3.env_state.feedback == ""
        assert s3.env_state.location == ""
        assert s3.env_state.description == ""
        assert s3.env_state.inventory == ""
        assert s3.env_state.items == 0
        assert s3.env_state.score == 0
        assert s3.env_state.reward == 0.0
        assert s3.env_state.is_done is False
        assert s3.agent_state.summary == ""
        assert s3.agent_state.plan == ""
        assert s3.agent_state.memory == ""
        assert s3.agent_state.thought == ""
        assert s3.agent_state.action == ""



