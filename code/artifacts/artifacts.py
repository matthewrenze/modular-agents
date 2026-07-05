import os
import time
import shutil
from params.parameters import Parameters


class Artifacts:
    def __init__(self):
        self.folder_path = "../data/artifacts"

    def get_agent_folder_path(self, params: Parameters) -> str:
        return f"{self.folder_path}/{params.version}/{params.split_name}/{params.model_name}/{params.agent_name}"

    def get_eval_folder_path(self, params: Parameters) -> str:
        return f"{self.get_agent_folder_path(params)}/{params.eval_name}"

    def get_episode_folder_path(self, params: Parameters) -> str:
        return f"{self.get_eval_folder_path(params)}/episode-{params.episode_id}"

    def get_agent_file_name(self, params: Parameters, suffix: str) -> str:
        return f"{params.version} - {params.split_name} - {params.model_name} - {params.agent_name} - {suffix}"

    def get_eval_file_name(self, params: Parameters, suffix: str) -> str:
        return self.get_agent_file_name(params, f"{params.eval_name} - {suffix}")

    def get_file_name(self, params: Parameters, suffix: str) -> str:
        return self.get_eval_file_name(params, f"episode-{params.episode_id} - {suffix}")

    def create_episode(self, params: Parameters) -> str:
        folder_path = self.get_episode_folder_path(params)
        os.makedirs(folder_path, exist_ok=True)
        return folder_path

    def delete_episode(self, params: Parameters):
        # Retried with backoff: Dropbox transiently locks files while syncing
        folder_path = self.get_episode_folder_path(params)
        if not os.path.exists(folder_path):
            return
        for attempt in range(5):
            try:
                shutil.rmtree(folder_path)
                break
            except PermissionError:
                if attempt == 4:
                    raise
                time.sleep(2 ** attempt)
