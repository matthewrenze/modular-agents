import os
import pandas as pd
from filelock import FileLock
from artifacts.artifacts import Artifacts
from logs.console import warn
from results.result_row import ResultRow
from params.parameters import Parameters

class ResultsManager:
    def __init__(self, artifacts: Artifacts):
        self.artifacts = artifacts
        self.results = pd.DataFrame()

    def create(self, params: Parameters):
        row = ResultRow()
        row.version = params.version
        row.split_name = params.split_name
        row.model_name = params.model_name
        row.agent_name = params.agent_name
        row.eval_name = params.eval_name
        return row

    def add(self, row):
        self.results = pd.concat([self.results, pd.DataFrame([row.__dict__])], ignore_index=True)

    def get_table(self):
        return self.results

    def get_file_path(self, params: Parameters):
        folder_path = self.artifacts.get_eval_folder_path(params)
        file_name = self.artifacts.get_eval_file_name(params, "results.csv")
        return f"{folder_path}/{file_name}"

    def load(self, params: Parameters):
        file_path = self.get_file_path(params)
        self.results = pd.read_csv(file_path)

    def save(self, params: Parameters, row):
        file_path = self.get_file_path(params)
        folder_path = os.path.dirname(file_path)
        lock_path = file_path + ".lock"

        os.makedirs(folder_path, exist_ok=True)

        lock = FileLock(lock_path, timeout=60)

        try:
            with lock:

                # Load the existing results
                if not os.path.exists(file_path):
                    results = pd.DataFrame()
                else:
                    results = pd.read_csv(file_path)

                # Drop any existing row for this episode
                if not results.empty:
                    results = results[results["episode"] != params.episode_id]

                # Append the new row and sort by episode
                results = pd.concat([results, pd.DataFrame([row.__dict__])], ignore_index=True)
                results.sort_values(by=["episode"], inplace=True)

                # Save the results atomically
                temp_path = file_path + ".tmp"
                results.to_csv(temp_path, index=False)
                os.replace(temp_path, file_path)

        except Exception as e:
            date_time = pd.Timestamp.now().strftime("%Y-%m-%d_%H-%M-%S")
            fallback_file_path = f"{folder_path}/results-{date_time}.csv"
            pd.DataFrame([row.__dict__]).to_csv(fallback_file_path, index=False)
            warn(f"Failed to save results row ({type(e).__name__}: {e}). Row saved to fallback file: {fallback_file_path}")

    def exists(self, params: Parameters):
        file_path = self.get_file_path(params)

        if not os.path.exists(file_path):
            return False

        results = pd.read_csv(file_path)
        if results.empty:
            return False

        return (results["episode"] == params.episode_id).any()
