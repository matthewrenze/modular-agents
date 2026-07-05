import os
from artifacts.artifacts import Artifacts
from params.parameters import Parameters

class LogReader:

    def __init__(self, artifacts: Artifacts):
        self.artifacts = artifacts

    def read(self, params: Parameters):

        # Create file path
        folder_path = self.artifacts.get_episode_folder_path(params)
        file_name = self.artifacts.get_file_name(params, "log.txt")
        file_path = f"{folder_path}/{file_name}"

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Log file not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()

        return content
