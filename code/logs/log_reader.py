import os
from params.parameters import Parameters

class LogReader:
    
    def read(self, params: Parameters, episode_id):

        folder_path = f"../data/logs/{params.model_name} - {params.agent_name} - {params.eval_name}"
        file_path = f"{folder_path}/{episode_id}.txt"

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Log file not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()

        return content