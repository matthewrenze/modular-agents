"""Replay every tw-long game's walkthrough through TextWorldEnv.

Both long-game generators push TextWorld past its intended limits, so compiling is
not evidence of solvability: every walkthrough must replay to full score before any
billable run. Uses the harness's real TextWorldEnv (not raw textworld.gym) so the
.json metadata sidecar and max-items handling are proven on these games too.
Prints the solution-step distribution per eval file.

Run from evals/: python validate_tw_long.py [--set train|test] [--eval tw-long-cook]
"""
import os
import sys
import glob
import argparse
from types import SimpleNamespace

import pandas as pd

sys.path.insert(0, "../code")
from environments.textworld_env import TextWorldEnv

# Parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("--set", choices=["train", "test"])
parser.add_argument("--eval")
args = parser.parse_args()

task_sets = [args.set] if args.set else ["train", "test"]

failures = []
for task_set in task_sets:

    # Find the eval files to validate
    pattern = args.eval or "tw-long-*"
    eval_file_paths = sorted(glob.glob(f"../data/evals/{task_set}/tw-long/{pattern}.jsonl"))

    for eval_file_path in eval_file_paths:
        eval_name = os.path.basename(eval_file_path).replace(".jsonl", "")
        evals = pd.read_json(eval_file_path, lines=True)

        # Report the solution-step distribution
        steps = evals["solution_steps"]
        counts = ", ".join(f"{s}×{c}" for s, c in steps.value_counts().sort_index().items())
        print(f"{task_set} {eval_name}: {len(evals)} tasks, solution steps "
              f"min={steps.min()} median={int(steps.median())} max={steps.max()}")
        print(f"  distribution: {counts}")

        # Replay every walkthrough to full score
        params = SimpleNamespace(max_steps=int(steps.max()) + 10)
        env = TextWorldEnv(params, evals)
        for episode_id in range(1, len(evals) + 1):
            row = evals.iloc[episode_id - 1]
            task_state, env_state = env.reset(episode_id)
            for action in row["solution"].split(", "):
                env_state = env.step(action)
            if env_state.score != task_state.max_score or not env_state.is_done:
                failures.append((task_set, eval_name, row["id"],
                                 env_state.score, task_state.max_score))
                print(f"  FAIL task-{row['id']}: score {env_state.score}/{task_state.max_score}, "
                      f"is_done={env_state.is_done}")
            if episode_id % 10 == 0:
                print(f"  replayed {episode_id}/{len(evals)}", flush=True)

if failures:
    print(f"\n{len(failures)} walkthrough(s) FAILED to replay to full score.")
    sys.exit(1)
print("\nAll walkthroughs replayed to full score.")
