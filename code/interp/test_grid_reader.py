import io
import pandas as pd
from artifacts.artifacts import Artifacts
from params.parameters import Parameters
from interp import grid_reader
from interp.grid_reader import GridReader

RESULTS_CSV = """\
version,split_name,model_name,model_version,agent_name,eval_name,episode,task,revised_task,success,reward,score,max_score,steps,max_steps,max_steps_hit,solution_steps,cached_tokens,input_tokens,reasoning_tokens,output_tokens,total_tokens,input_cost,output_cost,total_cost,start_time,end_time,sleep_time,total_time,reward_per_step,reward_per_token,error
v6.0,test,gpt-5.4,,modular-full,tw-coin-1,10,task 1,,True,1.0,1,1,11,20,False,10,0,100,0,50,150,0.1,0.2,0.3,,,0,60,0.09,0.006,
v6.0,test,gpt-5.4,,modular-full,tw-coin-1,20,task 1,,False,0.0,0,1,20,20,True,10,0,100,0,50,150,0.1,0.2,0.3,,,0,60,0.0,0.0,
"""

# Fake artifact tree: folder path -> directory entries
TREE = {
    "root/v6.0/test": ["claude-sonnet-4-6", "gpt-5.4"],
    "root/v6.0/test/claude-sonnet-4-6": ["modular-full"],
    "root/v6.0/test/claude-sonnet-4-6/modular-full": ["tw-simple-1"],
    "root/v6.0/test/claude-sonnet-4-6/modular-full/tw-simple-1": ["episode-10", "results.csv"],
    "root/v6.0/test/gpt-5.4": ["modular-full", "react-kn"],
    "root/v6.0/test/gpt-5.4/modular-full": ["tw-coin-1"],
    "root/v6.0/test/gpt-5.4/modular-full/tw-coin-1": ["episode-10", "episode-20", "episode-100", "results.csv"],
    "root/v6.0/test/gpt-5.4/react-kn": ["tw-coin-1"],
    "root/v6.0/test/gpt-5.4/react-kn/tw-coin-1": ["episode-10"],
}

class TestGridReader:
    def test_list_episodes(self, monkeypatch):

        # Fake the folder listings
        monkeypatch.setattr(grid_reader.os, "listdir", lambda folder_path: TREE[folder_path])
        artifacts = Artifacts()
        artifacts.folder_path = "root"

        # List the episodes
        reader = GridReader(artifacts)
        episodes = reader.list_episodes("v6.0", "test")
        assert len(episodes) == 5

        # Verify the identity fields and sort order (model, agent, eval, then numeric episode)
        first = episodes[0]
        assert first == Parameters(version="v6.0", split_name="test", model_name="claude-sonnet-4-6",
                                   agent_name="modular-full", eval_name="tw-simple-1", episode_id=10)
        gpt = [p for p in episodes if p.model_name == "gpt-5.4" and p.agent_name == "modular-full"]
        assert [p.episode_id for p in gpt] == [10, 20, 100]

    def test_read_results(self, monkeypatch):
        params = Parameters(version="v6.0", split_name="test", model_name="gpt-5.4",
                            agent_name="modular-full", eval_name="tw-coin-1")
        artifacts = Artifacts()
        artifacts.folder_path = "root"

        # Fake the results read (capture the real parser before patching the module's)
        real_read_csv = pd.read_csv
        def fake_read_csv(file_path):
            assert file_path == ("root/v6.0/test/gpt-5.4/modular-full/tw-coin-1/"
                                 "v6.0 - test - gpt-5.4 - modular-full - tw-coin-1 - results.csv")
            return real_read_csv(io.StringIO(RESULTS_CSV))
        monkeypatch.setattr(grid_reader.pd, "read_csv", fake_read_csv)

        # Read the results
        reader = GridReader(artifacts)
        results = reader.read_results(params)
        assert len(results) == 2
        assert list(results["episode"]) == [10, 20]
        assert list(results["success"]) == [True, False]
        assert list(results["error"]) == ["", ""]
