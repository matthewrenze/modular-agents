import os
from params.parameters import Parameters

class AnalysisWriter:
    def write(self, params: Parameters, analysis: str):

        # Create the folder
        folder_path = f"../data/analysis"
        os.makedirs(folder_path, exist_ok=True)

        # Write the analysis
        file_path = f"{folder_path}/{params.model_name} - {params.agent_name}.txt"
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(analysis)