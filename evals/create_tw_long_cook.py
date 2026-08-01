"""Generate the tw-long-cook eval: single long cooking tasks (~182 solution steps).

Recipe 16 / go 12 / all skills saturates the cooking generator's 38-food pool at
~182 walkthrough steps (see evals/x_probe_long_lengths.py, verified 2026-07-26).
Two upstream limits are worked around:
  1. cooking.make() asserts nb_ingredients <= 5 — run under `python -O` to strip it.
  2. Recipe >= 8 exceeds Inform 6's MAX_EXPRESSION_NODES — patch_inform6_limits().

Run from evals/: python -O create_tw_long_cook.py [--set train|test] [--start N] [--end N]
"""
import os
import sys
import json
import fcntl
import argparse
import textworld.challenges.tw_cooking.cooking
from inform6_limits import patch_inform6_limits
from log import Log

# Require python -O: cooking.make() asserts nb_ingredients <= 5 otherwise
if __debug__:
    sys.exit("Run with `python -O`: cooking.make() asserts nb_ingredients <= 5 otherwise.")

# Parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("--set", choices=["train", "test"])
parser.add_argument("--start", type=int)
parser.add_argument("--end", type=int)
args = parser.parse_args()

# Set default parameters
num_tasks = 100
eval_name = "tw-long-cook"

# Set the game settings
settings = {
    "recipe": 16, "take": 16, "go": 12,
    "open": True, "cook": True, "cut": True, "drop": True}

# Set optional parameters
task_sets  = [args.set]   if args.set   else ["train", "test"]
start_task = args.start or 1
end_task   = args.end   or num_tasks

# Patch the Inform 6 memory limits
patch_inform6_limits()

for task_set in task_sets:

    # Set folder paths
    eval_folder_path = f"../data/evals/{task_set}/tw-long"
    game_folder_path = f"../data/evals/{task_set}/tw-long/files"

    # Create the target files folders
    os.makedirs(eval_folder_path, exist_ok=True)
    os.makedirs(game_folder_path, exist_ok=True)

    log = Log(f"{task_set}-long-cook")
    eval_file_path = f"{eval_folder_path}/{eval_name}.jsonl"

    for task_id in range(start_task, end_task + 1):
        log.write(f"Creating {task_set} {eval_name} task-{task_id} ...")

        # Set random seed (train and test draw from disjoint seed ranges)
        random_base = 0 if task_set == "train" else 1000
        random_seed = random_base + task_id

        # Set path for the game
        game_file_name = f"{eval_name}-{task_id}.ulx"
        game_file_path = game_folder_path + "/" + game_file_name

        # Delete the old game
        if os.path.exists(game_file_path):
            os.remove(game_file_path)

        # Set the settings
        task_settings                = settings.copy()
        task_settings["split"]       = task_set
        task_settings["recipe_seed"] = random_seed
        log.write(f"  Settings: {task_settings}")

        # Set the options
        options = textworld.GameOptions()
        options.path = game_file_path
        options.seeds = {
            "map": random_seed,
            "objects": random_seed,
            "quest": random_seed,
            "grammar": random_seed}

        # Create the game
        game = textworld.challenges.cooking.make(task_settings, options)

        # Compile the game
        game_file_path = textworld.generator.compile_game(game, options)

        # Add the task
        task = {
            "id": task_id,
            "task": game.objective,
            "solution": ", ".join(game.walkthrough),
            "solution_steps": len(game.walkthrough),
            "file_path": game_file_path
        }
        log.write(f"  Solution steps: {task['solution_steps']}")

        # Upsert into the existing JSONL file
        with open(eval_file_path + ".lock", "w") as lock_file:
            fcntl.flock(lock_file, fcntl.LOCK_EX)
            existing_tasks = {}
            if os.path.exists(eval_file_path):
                with open(eval_file_path, "r") as f:
                    for line in f:
                        row = json.loads(line)
                        existing_tasks[row["id"]] = row
            existing_tasks[task["id"]] = task
            with open(eval_file_path, "w") as f:
                for row in sorted(existing_tasks.values(), key=lambda x: x["id"]):
                    f.write(json.dumps(row) + "\n")
