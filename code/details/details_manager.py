import os
import pandas as pd
from details.details_row import DetailsRow
from params.parameters import Parameters

class DetailsManager:
    def __init__(self, params: Parameters):
        self.folder_path = "../data/artifacts"
        self.details = pd.DataFrame()
        self.params = params
        self.episode_id = params.episode_id

    def create(self):
        row = DetailsRow()
        return row

    def add(self, row):
        self.details = pd.concat([self.details, pd.DataFrame([row.__dict__])], ignore_index=True)

    def get_table(self):
        return self.details

    def save(self):
        # Create the folder path
        split_name = self.params.split_name
        model_name = self.params.model_name
        agent_name = self.params.agent_name
        eval_name = self.params.eval_name
        episode_id = self.episode_id
        subfolder_name = f"/{split_name}/{model_name}/{agent_name}/{eval_name}/episode-{episode_id}"
        subfolder_path = f"{self.folder_path}/{subfolder_name}"

        # Create the folder if it doesn't exist
        os.makedirs(subfolder_path, exist_ok=True)

        # Create the file path
        file_name = f"{split_name} - {model_name} - {agent_name} - {eval_name} - episode-{episode_id} - details.csv"
        file_path = f"{subfolder_path}/{file_name}"

        # Save the details
        self.details.to_csv(file_path, index=False)
