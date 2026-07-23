import os
import re
import pandas as pd
from artifacts.artifacts import Artifacts
from params.parameters import Parameters

class GridReader:
    def __init__(self, artifacts: Artifacts):
        self.artifacts = artifacts

    def list_episodes(self, version: str, split_name: str) -> list:
        # Walk artifacts/<version>/<split>/<model>/<agent>/<eval>/episode-<N>
        episodes = []
        split_path = f"{self.artifacts.folder_path}/{version}/{split_name}"
        for model_name in sorted(os.listdir(split_path)):
            model_path = f"{split_path}/{model_name}"
            for agent_name in sorted(os.listdir(model_path)):
                agent_path = f"{model_path}/{agent_name}"
                for eval_name in sorted(os.listdir(agent_path)):
                    eval_path = f"{agent_path}/{eval_name}"
                    episode_ids = []
                    for entry in os.listdir(eval_path):
                        match = re.fullmatch(r"episode-(\d+)", entry)
                        if match:
                            episode_ids.append(int(match.group(1)))
                    for episode_id in sorted(episode_ids):
                        episodes.append(Parameters(version=version, split_name=split_name,
                                                   model_name=model_name, agent_name=agent_name,
                                                   eval_name=eval_name, episode_id=episode_id))
        return episodes

    def read_results(self, params: Parameters) -> pd.DataFrame:
        folder_path = self.artifacts.get_eval_folder_path(params)
        file_name = self.artifacts.get_eval_file_name(params, "results.csv")
        results = pd.read_csv(f"{folder_path}/{file_name}")
        results["error"] = results["error"].fillna("")
        return results
