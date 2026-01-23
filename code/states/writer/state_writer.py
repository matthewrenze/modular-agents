import os
import yaml
from common.parameters import Parameters
from states.global_state import GlobalState


class StateWriter:

    def write(self, state: GlobalState, params: Parameters, episode_id: int):

        # Create the folder
        folder_path = f"../data/states/{params.agent_name} - {params.model_name} - {params.eval_name}"
        os.makedirs(folder_path, exist_ok=True)

        # Write the file
        file_path = f"{folder_path}/{episode_id}.yaml"
        with open(file_path, "w", encoding="utf-8") as file:
            yaml.safe_dump(
                state.model_dump(mode="python"),
                file,
                sort_keys=False,
                default_flow_style=False,
                allow_unicode=True)
