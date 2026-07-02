import os
import pandas as pd
from filelock import FileLock
from logs.console import warn
from summaries.summary_row import SummaryRow

class SummaryManager:

    def __init__(self):
        self.file_path = "../data/summaries.csv"
        self.lock_path = self.file_path + ".lock"

    def summarize(self, results):
        summary = SummaryRow()
        summary.version = results["version"].iloc[0]
        summary.split_name = results["split_name"].iloc[0]
        summary.model_name = results["model_name"].iloc[0]
        summary.agent_name = results["agent_name"].iloc[0]
        summary.eval_name = results["eval_name"].iloc[0]
        summary.episodes = len(results)
        summary.successes = len(results[results["reward"] == 1.0])
        summary.failures = len(results[results["reward"] < 1.0])
        summary.errors = len(results[results["error"] != ""])
        summary.accuracy = summary.successes / summary.episodes
        summary.total_reward = results["reward"].sum()
        summary.total_steps = results["steps"].sum()
        summary.max_steps_hit = results["max_steps_hit"].sum()
        summary.model_version = results["model_version"].iloc[0]
        summary.cached_tokens = results["cached_tokens"].sum()
        summary.input_tokens = results["input_tokens"].sum()
        summary.reasoning_tokens = results["reasoning_tokens"].sum()
        summary.output_tokens = results["output_tokens"].sum()
        summary.total_tokens = results["total_tokens"].sum()
        summary.input_cost = results["input_cost"].sum()
        summary.output_cost = results["output_cost"].sum()
        summary.total_cost = results["total_cost"].sum()
        summary.total_time = results["total_time"].sum()
        summary.avg_reward_per_episode = summary.total_reward / summary.episodes if summary.episodes > 0 else 0
        summary.avg_reward_per_step = results["reward_per_step"].mean()
        summary.avg_reward_per_token = results["reward_per_token"].mean()
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

                # HACK: Move the version, split_name, and model_name to the first columns
                summaries = summaries[["model_name"] + [c for c in summaries.columns if c != "model_name"]]
                summaries = summaries[["split_name"] + [c for c in summaries.columns if c != "split_name"]]
                summaries = summaries[["version"] + [c for c in summaries.columns if c != "version"]]

                # Sort the summaries
                summaries.sort_values(by=["version", "split_name", "model_name", "agent_name", "eval_name"], inplace=True)

                temp_path = self.file_path + ".tmp"
                summaries.to_csv(temp_path, index=False)
                os.replace(temp_path, self.file_path)


        except Exception as e:
            warn(f"Summary file is locked. Saving to temporary file.")
            date_time = pd.Timestamp.now().strftime("%Y-%m-%d_%H-%M-%S")
            temp_file_path = f"../data/summaries-{date_time}.csv"
            pd.DataFrame([summary.__dict__]).to_csv(temp_file_path, index=False)
