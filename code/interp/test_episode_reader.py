import io
import pandas as pd
from artifacts.artifacts import Artifacts
from params.parameters import Parameters
from states.global_state import GlobalState
from states.task_state import TaskState
from interp import episode_reader
from interp.episode_reader import EpisodeReader

DETAILS_CSV = """\
step_id,task,feedback,location,description,inventory,score,reward,is_done,summary,thought,action,error,cached_tokens,input_tokens,reasoning_tokens,output_tokens,total_tokens
1,,,Dish-Pit,description 1,nothing,0,0.0,False,summary 1,thought 1,go north,,0,10,0,5,15
2,,feedback 2,Steam Room,description 2,nothing,0,0.0,False,summary 2,thought 2,go north,,0,10,0,5,15
3,,feedback 3,Closet,description 3,nothing,0,0.0,False,summary 3,thought 3,go west,,0,10,0,5,15
"""

PREFIX = "v6.0 - test - gpt-5.4 - modular-full - tw-coin-1 - episode-10"

MESSAGE_FILES = {
    f"{PREFIX} - step-0 - actor - system-prompt.md": "system prompt",
    f"{PREFIX} - step-1 - actor.md": "actor 1",
    f"{PREFIX} - step-1 - summarizer.md": "summarizer 1",
    f"{PREFIX} - step-2 - actor.md": "actor 2",
    f"{PREFIX} - step-2 - summarizer.md": "summarizer 2",
    f"{PREFIX} - step-3 - actor.md": "actor 3",
}

class FakeStateReader:
    def __init__(self, state: GlobalState):
        self.state = state
        self.file_path = None

    def read(self, file_path: str) -> GlobalState:
        self.file_path = file_path
        return self.state

class TestEpisodeReader:
    def test_read(self, monkeypatch):
        params = Parameters(version="v6.0", split_name="test", model_name="gpt-5.4",
                            agent_name="modular-full", eval_name="tw-coin-1", episode_id=10)
        artifacts = Artifacts()
        artifacts.folder_path = "root"
        episode_path = "root/v6.0/test/gpt-5.4/modular-full/tw-coin-1/episode-10"

        # Fake the state reader (constructor-injected)
        state = GlobalState(task_state=TaskState(task="task 1"), plan="- [ ] step 1",
                            memories={"kitchen": "rooms = {south = bar}"})
        state_reader = FakeStateReader(state)

        # Fake the details read (capture the real parser before patching the module's)
        real_read_csv = pd.read_csv
        def fake_read_csv(file_path, keep_default_na):
            assert file_path == f"{episode_path}/{PREFIX} - details.csv"
            assert keep_default_na is False
            return real_read_csv(io.StringIO(DETAILS_CSV), keep_default_na=False)
        monkeypatch.setattr(episode_reader.pd, "read_csv", fake_read_csv)

        # Fake the messages folder listing and file reads
        def fake_listdir(folder_path):
            assert folder_path == f"{episode_path}/messages"
            return list(MESSAGE_FILES)
        monkeypatch.setattr(episode_reader.os, "listdir", fake_listdir)

        def fake_open(file_path, mode="r", encoding=None, *args, **kwargs):
            file_name = file_path.rsplit("/", 1)[1]
            return io.StringIO(MESSAGE_FILES[file_name])
        monkeypatch.setattr(episode_reader, "open", fake_open, raising=False)

        # Read the episode
        reader = EpisodeReader(artifacts, state_reader)
        extract = reader.read(params)

        # Verify the state read
        assert state_reader.file_path == f"{episode_path}/{PREFIX} - state.yaml"
        assert extract.params == params
        assert extract.state.task_state.task == "task 1"
        assert extract.state.plan == "- [ ] step 1"
        assert extract.state.memories == {"kitchen": "rooms = {south = bar}"}

        # Verify the details
        assert len(extract.details) == 3
        assert list(extract.details["action"]) == ["go north", "go north", "go west"]
        assert extract.details["feedback"][0] == ""

        # Verify the last-2-steps messages (step 1 and the system prompts are excluded)
        assert sorted(extract.last_messages.keys()) == [2, 3]
        assert extract.last_messages[2] == {"actor": "actor 2", "summarizer": "summarizer 2"}
        assert extract.last_messages[3] == {"actor": "actor 3"}
