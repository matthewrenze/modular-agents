import pandas as pd
from artifacts.artifacts import Artifacts
from details.details_row import DetailsRow
from params.parameters import Parameters

class DetailsManager:
    def __init__(self, artifacts: Artifacts, params: Parameters):
        self.artifacts = artifacts
        self.details = pd.DataFrame()
        self.params = params

    def create(self):
        row = DetailsRow()
        return row

    def add(self, row):
        self.details = pd.concat([self.details, pd.DataFrame([row.__dict__])], ignore_index=True)

    def get_table(self):
        return self.details

    def save(self):
        # Create the folder if it doesn't exist
        folder_path = self.artifacts.create_episode(self.params)

        # Create the file path
        file_name = self.artifacts.get_file_name(self.params, "details.csv")
        file_path = f"{folder_path}/{file_name}"

        # Save the details
        self.details.to_csv(file_path, index=False)
