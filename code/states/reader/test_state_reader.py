import io
from states.reader import state_reader
from states.reader.state_reader import StateReader

TEST_YAML = """
task_state:
    task: task 1
    step_id: 3
    max_steps: 99
    max_items: 10
    max_score: 2
    max_reward: 1.0
    success: false
memories:
 1: memory 1
 2: memory 2
step_history:
  - step_id: 1
    env_state:
      location: location 1
      description: description 1
      inventory: inventory 1
      items: 1
      max_items: 5
      score: 1
      max_score: 2
      reward: 0.50
      max_reward: 1.0
      is_done: false
    agent_state:
      summary: summary 1
      memory: |
        create: memory 1
        delete: 1
      thought: thought 1
      action: action 1
  - step_id: 2
    env_state:
      feedback: feedback 2
      location: location 2
      description: description 2.
      inventory: inventory 2
      items: 2
      max_items: 10
      score: 2
      max_score: 2
      reward: 1.0
      max_reward: 1.0
      is_done: true
    agent_state:
      summary: summary 2
      memory: |
        create: memory 2
        create: memory 3
        delete: 2
        delete: 3
      thought: thought 2
      action: action 2
  - step_id: 3
    env_state: {}
    agent_state: {}
"""

class TestStateReader:
    def test_read(self, monkeypatch):

        # Create a fake open function to mock file reading
        def fake_open(file_path, mode="r", encoding=None, *args, **kwargs):
            assert file_path == "states/reader/test_state.yaml"
            assert mode == "r"
            assert encoding == "utf-8"
            return io.StringIO(TEST_YAML)

        monkeypatch.setattr(state_reader, "open", fake_open, raising=False)

        # Create the state reader
        reader = StateReader()
        state = reader.read("states/reader/test_state.yaml")

        # Verify task state
        t1 = state.task_state
        assert t1.task == "task 1"
        assert t1.step_id == 3
        assert t1.max_steps == 99
        assert t1.max_items == 10
        assert t1.max_score == 2
        assert t1.max_reward == 1.0
        assert t1.success is False

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
        assert s1.agent_state.memory == "create: memory 1\ndelete: 1\n"
        assert s1.agent_state.thought == "thought 1"
        assert s1.agent_state.action == "action 1"

        # Verify the second step
        s2 = state.step_history[1]
        assert s2.step_id == 2
        assert s2.env_state.feedback == "feedback 2"
        assert s2.env_state.location == "location 2"
        assert s2.env_state.description == "description 2."
        assert s2.env_state.inventory == "inventory 2"
        assert s2.env_state.items == 2
        assert s2.env_state.score == 2
        assert s2.env_state.reward == 1.0
        assert s2.env_state.is_done is True
        assert s2.agent_state.summary == "summary 2"
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
        assert s3.agent_state.thought == ""
        assert s3.agent_state.action == ""
        assert s3.agent_state.summary == ""


