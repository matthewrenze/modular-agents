import json
import argparse
from pathlib import Path
from log import Log

# Parse the arguments
parser = argparse.ArgumentParser()
parser.add_argument("--set", choices=["train", "test"], required=True)
args = parser.parse_args()

# Create the log
log = Log(f"tw-quick-1-{args.set}")

# Get the base folder
base_folder_path = Path(__file__).parent.parent / "data" / "evals" / args.set / "tw-cooking"

# Create the source task sets (file name, start ID, end ID)
source_tasks = [
    (base_folder_path / "tw-cooking-2.jsonl", 30, 99),
    (base_folder_path / "tw-cooking-3.jsonl", 20, 49),
]

# Read tasks from the source sets and filter by ID
tasks = []
for jsonl_path, id_start, id_end in source_tasks:
    with open(jsonl_path) as f:
        for line in f:
            task = json.loads(line)
            if id_start <= task["id"] <= id_end:
                tasks.append(task)

# Reassign IDs to be sequential starting from 1
for new_id, task in enumerate(tasks, 1):
    task["id"] = new_id

# Write the tasks to the output file
out_dir = Path(__file__).parent.parent / "data" / "evals" / args.set / "tw-quick"
out_dir.mkdir(exist_ok=True)
out_path = out_dir / "tw-quick-1.jsonl"

# Write tasks to the output JSONL file
with open(out_path, "w") as f:
    for task in tasks:
        f.write(json.dumps(task) + "\n")

# Log the result
log.write(f"Written {len(tasks)} tasks to {out_path}")
