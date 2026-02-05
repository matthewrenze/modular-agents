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
        assert len(state.plan) == 2
        p1 = state.plan[0]
        assert p1.id == 1
        assert p1.status == "done"
        assert p1.label == "step 1"
        p2 = state.plan[1]
        assert p2.id == 2
        assert p2.status == "todo"
        assert p2.label == "step 2"

        # Verify memories
        assert len(state.memories) == 2
        assert state.memories[1] == "memory 1"
        assert state.memories[2] == "memory 2"

        # Verify step history
        assert len(state.step_history) == 3

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
        assert s1.agent_state.plan == "add: plan 1\ninsert: 2 = plan 2\nupdate: 3 = plan 3\n"
        assert s1.agent_state.memory == "create: memory 1\ndelete: 1\n"
        assert s1.agent_state.thought == "thought 1"
        assert s1.agent_state.action == "action 1"

        # Verify the second step
        s2 = state.step_history[1]
        assert s2.step_id == 2
        assert s2.env_state.feedback == "feedback 2"
        assert s2.env_state.location == "location 2"
        assert s2.env_state.description == "description 2"
        assert s2.env_state.inventory == "inventory 2"
        assert s2.env_state.items == 2
        assert s2.env_state.score == 2
        assert s2.env_state.reward == 1.0
        assert s2.env_state.is_done is True
        assert s2.agent_state.summary == "summary 2"
        assert s2.agent_state.plan == "mark: 4\ndelete: 5\ndelete: 6\n"
        assert s2.agent_state.memory == "create: memory 2\ncreate: memory 3\ndelete: 2\ndelete: 3\n"
        assert s2.agent_state.thought == "thought 2"
        assert s2.agent_state.action == "action 2"

        # Verify the defaults (third step)
        s3 = state.step_history[2]
        assert s3.step_id == 3
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



