import os
import json
import fcntl
import argparse
import textworld.challenges.tw_coin_collector
from log import Log

# Parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("--set", choices=["train", "test"])
parser.add_argument("--level", type=int, choices=[1, 2, 3])
parser.add_argument("--start", type=int)
parser.add_argument("--end", type=int)
args = parser.parse_args()

# Set default parameters
num_tasks = 100

# Set optional parameters
task_sets  = [args.set]   if args.set   else ["train", "test"]
levels     = [args.level] if args.level else [1, 2, 3]
start_task = args.start or 1
end_task   = args.end   or num_tasks

for task_set in task_sets:

    # Set folder paths
    eval_folder_path = f"../data/evals/{task_set}/tw-coin"
    game_folder_path = f"../data/evals/{task_set}/tw-coin/files"

    # Create the target files folders
    os.makedirs(eval_folder_path, exist_ok=True)
    os.makedirs(game_folder_path, exist_ok=True)

    for level_id in levels:

        log = Log(f"{task_set}-coin-{level_id}")
        eval_file_name = f"tw-coin-{level_id}.jsonl"
        eval_file_path = eval_folder_path + "/" + eval_file_name

        for task_id in range(start_task, end_task + 1):
            log.write(f"Creating {task_set} tw-coin-{level_id} task-{task_id} ...")

            # Set random seed for reproducibility
            random_base = 0 if task_set == "train" else 1000
            random_seed = random_base + task_id

            # Set path for the game
            game_file_name = f"tw-coin-{level_id}-{task_id}.ulx"
            game_file_path = game_folder_path + "/" + game_file_name

            # Delete the old game
            if os.path.exists(game_file_path):
                os.remove(game_file_path)

            # Set the settings
            sublevel   = (task_id - 1) // 10 + 1
            game_level = (level_id - 1) * 100 + task_id
            settings   = {"level": game_level}
            log.write(f"  Settings: {settings}")
            log.write(f"  Sublevel: {sublevel}")

            # Set the options
            options = textworld.GameOptions()
            options.path = game_file_path
            options.seeds = {
                "map": random_seed,
                "objects": random_seed,
                "quest": random_seed,
                "grammar": random_seed}

            # Create the game
            game = textworld.challenges.coin_collector.make(settings, options)

            # Compile the game
            game_file_path = textworld.generator.compile_game(game, options)

            # Add the task
            task = {
                "id": task_id,
                "level": level_id,
                "sublevel": sublevel,
                "task": game.objective,
                "solution": ", ".join(game.walkthrough),
                "solution_steps": len(game.walkthrough),
                "file_path": game_file_path
            }

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
