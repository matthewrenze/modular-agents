import os
import json
import fcntl
import argparse
import textworld.challenges.tw_treasure_hunter
from log import Log

# The main create_tw_treasure script gets really slow from level 3, task 90-100.
# I think it's some kind of issue with the random seed generating maps that don't have valid paths.
# Creating them one at a time seems to help make the process go MUCH faster.
# Level 3, task 94 is by far the slowest one, so I have a hack <below> to change the random seed to 194.
# Use --level 3 --start 90 --end 100 (or one task at a time) to generate these separately.

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

    eval_folder_path = f"../data/evals/{task_set}/tw-treasure"
    game_folder_path = f"../data/evals/{task_set}/tw-treasure/files"

    # Create the target files folders
    os.makedirs(eval_folder_path, exist_ok=True)
    os.makedirs(game_folder_path, exist_ok=True)

    for level_id in levels:

        log = Log(f"{task_set}-treasure-{level_id}")
        eval_file_name = f"tw-treasure-{level_id}.jsonl"
        eval_file_path = eval_folder_path + "/" + eval_file_name

        for task_id in range(start_task, end_task + 1):
            log.write(f"Creating {task_set} tw-treasure-{level_id} task-{task_id}...")

            # Set random seed
            random_base = 0 if task_set == "train" else 1000
            random_seed = random_base + task_id

            # HACK: task 94 is by far the slowest - bump the seed to avoid a bad map configuration
            if level_id == 3 and task_id == 94:
                random_seed += 100

            # Set the path
            game_file_name = f"tw-treasure-{level_id}-{task_id}.ulx"
            game_file_path = game_folder_path + "/" + game_file_name

            # Delete the old game
            if os.path.exists(game_file_path):
                os.remove(game_file_path)

            # Set the settings
            sublevel   = (task_id - 1) // 10 + 1
            game_level = ((level_id - 1) * 10) + ((task_id - 1) // 10 + 1)
            settings   = {"level": game_level}
            log.write(f"  Settings: {settings}")
            log.write(f"  Sublevel: {sublevel}")

            # HACK: to fix "Current map configuration doesn't permit quest of length: {n}"
            retry = True
            while retry:

                # Create the game
                try:

                    # Set the options
                    options = textworld.GameOptions()
                    options.path = game_file_path
                    options.seeds = {
                        "map": random_seed,
                        "objects": random_seed,
                        "quest": random_seed,
                        "grammar": random_seed}

                    game = textworld.challenges.treasure_hunter.make(settings, options)
                    retry = False

                except Exception as e:
                    retry = True
                    random_seed += 100
                    log.write(f"  *** Retry due to error: {e} ***")

            # Compile the game
            game_path = textworld.generator.compile_game(game, options)

            # Add the task
            task = {
                "id": task_id,
                "level": level_id,
                "sublevel": sublevel,
                "task": game.objective,
                "solution": ", ".join(game.walkthrough),
                "solution_steps": len(game.walkthrough),
                "file_path": game_path
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
