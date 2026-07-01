import os
import pandas as pd
from results.results_manager import ResultsManager
from summaries.summary_manager import SummaryManager

# Set paths
artifacts_folder_path = "../data/artifacts"
summary_file_path = "../data/summaries.csv"

# Find all result files
print("Finding result files...")
result_file_paths = []
for root, _, files in os.walk(artifacts_folder_path):
    for file_name in files:
        if file_name.endswith("results.csv"):
            result_file_paths.append(f"{root}/{file_name}".replace("\\", "/"))

# Sort paths for stable output
result_file_paths.sort()

# Create managers
summary_manager = SummaryManager()
summary_rows = []

# Summarize each results file
print(f"Summarizing {len(result_file_paths)} results files...")
for index, result_file_path in enumerate(result_file_paths, start=1):
    print(f"[{index}/{len(result_file_paths)}] Processing: {os.path.basename(result_file_path)}")
    results_manager = ResultsManager()
    results_manager.results = pd.read_csv(result_file_path)
    results_manager.results["error"] = results_manager.results["error"].fillna("")
    results = results_manager.get_table()
    summary_row = summary_manager.summarize(results)
    summary_rows.append(summary_row.__dict__)

# Save combined summary
summary_table = pd.DataFrame(summary_rows)

# Keep metadata first and order rows consistently
summary_table = summary_table[["version", "split_name", "model_name", "agent_name", "eval_name"] + [
    c for c in summary_table.columns if c not in ["version", "split_name", "model_name", "agent_name", "eval_name"]
]]
summary_table.sort_values(by=["split_name", "model_name", "agent_name", "eval_name"], inplace=True)

os.makedirs("../data", exist_ok=True)
summary_table.to_csv(summary_file_path, index=False)
print(f"Saved {len(summary_table)} summaries to {summary_file_path}")
