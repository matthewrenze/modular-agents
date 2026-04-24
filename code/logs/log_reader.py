import os
from params.parameters import Parameters

class LogReader:
    
    def read(self, params: Parameters, episode_id):

        # Create file path
        folder_path = f"../data/artifacts/{params.split_name}/{params.model_name}/{params.agent_name}/{params.eval_name}/episode-{episode_id}"
        file_name = f"{params.split_name} - {params.model_name} - {params.agent_name} - {params.eval_name} - episode-{episode_id} - log.txt"
        file_path = f"{folder_path}/{file_name}"

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Log file not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()

        return content