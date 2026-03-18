import os
import pandas as pd
from filelock import FileLock
from params.parameters import Parameters
from logs.console import warn
from summaries.summary_row import SummaryRow

class SummaryManager:

    def __init__(self):
        self.file_path = "../data/summaries.csv"
        self.lock_path = self.file_path + ".lock"

    def exists(self, params: Parameters):
        if not os.path.exists(self.file_path):
            return False

        summaries = pd.read_csv(self.file_path)
        if summaries is None or summaries.empty:
            return False

        model_matches = summaries["model_name"] == params.model_name
        agent_matches = summaries["agent_name"] == params.agent_name
        eval_matches = summaries["eval_name"] == params.eval_name
        all_matches = summaries[model_matches & agent_matches & eval_matches]

        return not all_matches.empty

    def summarize(self, results):
        summary = SummaryRow()
        summary.model_name = results["model_name"].iloc[0]
        summary.agent_name = results["agent_name"].iloc[0]
        summary.eval_name = results["eval_name"].iloc[0]
        summary.tasks = len(results)
        summary.successes = len(results[results["reward"] == 1.0])
        summary.failures = len(results[results["reward"] < 1.0])
        summary.errors = len(results[results["error"] != ""])
        summary.accuracy = summary.successes / summary.tasks
        summary.total_reward = results["reward"].sum()
        summary.total_steps = results["steps"].sum()
        summary.max_steps_hit = results["max_steps_hit"].sum()
        summary.cached_tokens = results["cached_tokens"].sum()
        summary.input_tokens = results["input_tokens"].sum()
        summary.reasoning_tokens = results["reasoning_tokens"].sum()
        summary.output_tokens = results["output_tokens"].sum()
        summary.total_tokens = results["total_tokens"].sum()
        summary.input_cost = results["input_cost"].sum()
        summary.output_cost = results["output_cost"].sum()
        summary.total_cost = results["total_cost"].sum()
        summary.total_time = results["total_time"].sum()
        summary.avg_reward_per_task = summary.total_reward / summary.tasks if summary.tasks > 0 else 0
        summary.avg_reward_per_step = summary.total_reward / summary.total_steps if summary.total_steps > 0 else 0
        summary.avg_reward_per_token = (summary.total_reward / summary.total_tokens) if summary.total_tokens > 0 else 0
        return summary

    def append(self, summary):

        lock = FileLock(self.lock_path, timeout=60)

        try:
            with lock:

                # Load the summaries
                if not os.path.exists(self.file_path):
                    summaries = pd.DataFrame()
                else:
                    summaries = pd.read_csv(self.file_path)

                # Append the new summary
                summaries = pd.concat([summaries, pd.DataFrame([summary.__dict__])], ignore_index=True)

                # HACK: Move the model_name to the first column
                summaries = summaries[["model_name"] + [c for c in summaries.columns if c != "model_name"]]

                # Sort the summaries
                summaries.sort_values(by=["model_name", "agent_name", "eval_name"], inplace=True)

                temp_path = self.file_path + ".tmp"
                summaries.to_csv(temp_path, index=False)
                os.replace(temp_path, self.file_path)


        except Exception as e:
            warn(f"Summary file is locked. Saving to temporary file.")
            date_time = pd.Timestamp.now().strftime("%Y-%m-%d_%H-%M-%S")
            temp_file_path = f"../data/summaries-{date_time}.csv"
            pd.DataFrame([summary.__dict__]).to_csv(temp_file_path, index=False)
