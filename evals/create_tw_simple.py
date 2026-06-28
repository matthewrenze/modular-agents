import os
import json
import fcntl
import argparse
import textworld.challenges.tw_simple.simple
from log import Log

# NOTE: There is a bug when using goal verbosity of "brief" or "none"
#       It says the goal is to "grill" an item instead of putting it on the stove
#       Do not use "brief" or "none" goal verbosity -- only use "detailed".

# Parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("--set", choices=["train", "test"])
parser.add_argument("--start", type=int)
parser.add_argument("--end", type=int)
args = parser.parse_args()

# Set default parameters
num_tasks        = 100
goal_verbosity   = "detailed"
reward_densities = ["dense", "balanced", "sparse"]
num_sublevels    = len(reward_densities)

# Set optional parameters
task_sets  = [args.set] if args.set else ["train", "test"]
start_task = args.start or 1
end_task   = args.end   or num_tasks

for task_set in task_sets:

    log = Log(f"{task_set}-simple")
    log.write(f"Creating {task_set} eval...")

    eval_folder_path = f"../data/evals/{task_set}/tw-simple"
    game_folder_path = f"../data/evals/{task_set}/tw-simple/files"

    # Create the target files folders
    os.makedirs(eval_folder_path, exist_ok=True)
    os.makedirs(game_folder_path, exist_ok=True)

    eval_file_name = f"tw-simple-1.jsonl"
    eval_file_path = eval_folder_path + "/" + eval_file_name

    for task_id in range(start_task, end_task + 1):

        # Set level and sublevel
        level_id    = 1
        sublevel_id = min((task_id - 1) // (num_tasks // num_sublevels) + 1, num_sublevels)

        log.write(f"Creating {task_set} tw-simple-{level_id} task-{task_id} ...")

        # Set random seed
        random_base = 0 if task_set == "train" else 1000
        random_seed = random_base + task_id

        # Set path for the game
        game_file_name = f"tw-simple-{level_id}-{task_id}.ulx"
        game_file_path = game_folder_path + "/" + game_file_name

        # Delete the old game
        if os.path.exists(game_file_path):
            os.remove(game_file_path)

        # Get the reward density and goal verbosity
        goal_verbosity_text = goal_verbosity
        reward_density_text = reward_densities[sublevel_id - 1]

        # Set the settings
        settings = {
            "goal": goal_verbosity_text,
            "rewards": reward_density_text,
            "test": False}
        log.write(f"  Sublevel: {sublevel_id}")
        log.write(f"  Settings: {settings}")

        # Set the options
        options = textworld.GameOptions()
        options.path = game_file_path
        options.seeds = {
            "map": random_seed,
            "objects": random_seed,
            "quest": random_seed,
            "grammar": random_seed}

        # Create the game
        game = textworld.challenges.simple.make(settings, options)

        # Compile the game
        game_path = textworld.generator.compile_game(game, options)

        # Add the eval metadata
        eval_row = {
            "id": task_id,
            "level": level_id,
            "sublevel": sublevel_id,
            "task": game.objective,
            "solution": ", ".join(game.walkthrough),
            "solution_steps": len(game.walkthrough),
            "file_path": game_path}

        # Upsert into the existing JSONL file
        with open(eval_file_path + ".lock", "w") as lock_file:
            fcntl.flock(lock_file, fcntl.LOCK_EX)
            existing_tasks = {}
            if os.path.exists(eval_file_path):
                with open(eval_file_path, "r") as f:
                    for line in f:
                        row = json.loads(line)
                        existing_tasks[row["id"]] = row
            existing_tasks[eval_row["id"]] = eval_row
            with open(eval_file_path, "w") as f:
                for row in sorted(existing_tasks.values(), key=lambda x: x["id"]):
                    f.write(json.dumps(row) + "\n")
