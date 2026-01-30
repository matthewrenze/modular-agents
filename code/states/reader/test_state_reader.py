import io
from states.reader import state_reader
from states.reader.state_reader import StateReader

TEST_YAML = """
task_state:
    task: Perform task 1.
    step_id: 3
    max_steps: 99
    max_items: 10
    max_score: 2
    max_reward: 1.0
    success: false
step_history:
  - step_id: 1
    env_state:
      location: Room 1
      description: You are in room 1.
      inventory: "You are carrying: item 1"
      items: 1
      max_items: 5
      score: 1
      max_score: 2
      reward: 0.50
      max_reward: 1.0
      is_done: false
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
      max_items: 10
      score: 2
      max_score: 2
      reward: 1.0
      max_reward: 1.0
      is_done: true
    agent_state:
      thought: I should do action 2.
      action: do action 2
      summary: Took action 2 in room 2.
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
        assert t1.task == "Perform task 1."
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
        assert s1.env_state.location == "Room 1"
        assert s1.env_state.description == "You are in room 1."
        assert s1.env_state.inventory == "You are carrying: item 1"
        assert s1.env_state.items == 1
        assert s1.env_state.score == 1
        assert s1.env_state.reward == 0.50
        assert s1.env_state.is_done is False
        assert s1.agent_state.thought == "I should do action 1."
        assert s1.agent_state.action == "do action 1"
        assert s1.agent_state.summary == "Took action 1 in room 1."

        # Verify the second step
        s2 = state.step_history[1]
        assert s2.step_id == 2
        assert s2.env_state.feedback == "You are now in room 2."
        assert s2.env_state.location == "Room 2"
        assert s2.env_state.description == "You are in room 2."
        assert s2.env_state.inventory == "You are carrying: item 1 and item 2"
        assert s2.env_state.items == 2
        assert s2.env_state.score == 2
        assert s2.env_state.reward == 1.0
        assert s2.env_state.is_done is True
        assert s2.agent_state.thought == "I should do action 2."
        assert s2.agent_state.action == "do action 2"
        assert s2.agent_state.summary == "Took action 2 in room 2."

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


