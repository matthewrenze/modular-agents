"""Generate the tw-long-coin eval: long coin-collector tasks (250 solution steps).

Calling coin_collector's make_game() directly with options.quest_length bypasses the
level cap in coin_collector.make() (see evals/x_probe_long_lengths.py, verified
2026-07-26). Games are distractor-free linear chains (nb_rooms = quest_length):
distractor modes exceed Inform 6's MAX_STATIC_DATA at ~450 rooms, and quest_length
300 fails in the Inform 7 stage, so 250 is the proven maximum. Needs neither of the
cooking generator's workarounds.

Run from evals/: python create_tw_long_coin.py [--set train|test] [--start N] [--end N]
"""
import os
import json
import fcntl
import argparse
import textworld
from textworld.challenges.tw_coin_collector.coin_collector import make_game
from log import Log

# Parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("--set", choices=["train", "test"])
parser.add_argument("--start", type=int)
parser.add_argument("--end", type=int)
args = parser.parse_args()

# Set default parameters
num_tasks = 100
eval_name = "tw-long-coin"
quest_length = 250

# Set optional parameters
task_sets  = [args.set]   if args.set   else ["train", "test"]
start_task = args.start or 1
end_task   = args.end   or num_tasks

for task_set in task_sets:

    # Set folder paths
    eval_folder_path = f"../data/evals/{task_set}/tw-long"
    game_folder_path = f"../data/evals/{task_set}/tw-long/files"

    # Create the target files folders
    os.makedirs(eval_folder_path, exist_ok=True)
    os.makedirs(game_folder_path, exist_ok=True)

    log = Log(f"{task_set}-long-coin")
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

        # Set the options
        options = textworld.GameOptions()
        options.path = game_file_path
        options.quest_length = quest_length
        options.nb_rooms = quest_length
        options.grammar.allowed_variables_numbering = True
        options.seeds = {
            "map": random_seed,
            "objects": random_seed,
            "quest": random_seed,
            "grammar": random_seed}
        log.write(f"  Settings: quest_length={quest_length}, mode=simple")

        # Create the game
        game = make_game("simple", options)

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
