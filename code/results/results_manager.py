import os
import pandas as pd
from results.result_row import ResultRow
from params.parameters import Parameters

class ResultsManager:
    def __init__(self):
        self.folder_path = "../data/artifacts"
        self.results = pd.DataFrame()

    def create(self, params: Parameters):
        row = ResultRow()
        row.agent_name = params.agent_name
        row.model_name = params.model_name
        row.eval_name = params.eval_name
        row.eval_size = params.eval_size
        return row

    def add(self, row):
        self.results = pd.concat([self.results, pd.DataFrame([row.__dict__])], ignore_index=True)

    def get_table(self):
        return self.results

    def load(self, params: Parameters):
        folder_path = f"{self.folder_path}/{params.model_name}/{params.agent_name}/{params.eval_name}"
        file_name = f"{params.model_name} - {params.agent_name} - {params.eval_name} - results.csv"
        file_path = f"{folder_path}/{file_name}"
        self.results = pd.read_csv(file_path)

    def save(self):
        # Create the folder if it doesn't exist
        os.makedirs(self.folder_path, exist_ok=True)

        # Create the file path
        model_name = self.results["model_name"].iloc[0]
        agent_name = self.results["agent_name"].iloc[0]
        eval_name = self.results["eval_name"].iloc[0]
        folder_path = f"{self.folder_path}/{model_name}/{agent_name}/{eval_name}"
        file_name = f"{model_name} - {agent_name} - {eval_name} - results.csv"
        file_path = f"{folder_path}/{file_name}"

        # Save the results
        self.results.to_csv(file_path, index=False)
