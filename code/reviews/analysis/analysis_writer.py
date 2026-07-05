import os
from artifacts.artifacts import Artifacts
from params.parameters import Parameters

class AnalysisWriter:
    def __init__(self, artifacts: Artifacts):
        self.artifacts = artifacts

    def write(self, params: Parameters, analysis: str):

        # Create the file path
        folder_path = self.artifacts.get_agent_folder_path(params)
        file_name = self.artifacts.get_agent_file_name(params, "analysis.txt")
        file_path = f"{folder_path}/{file_name}"

        # Write analysis
        os.makedirs(folder_path, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(analysis)