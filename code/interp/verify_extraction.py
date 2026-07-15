import os
import time
import pandas as pd
from artifacts.artifacts import Artifacts
from states.reader.state_reader import StateReader
from interp.episode_reader import EpisodeReader
from interp.grid_reader import GridReader

# Parameters
version = "v6.0"
split_name = "test"
output_folder = "../data/interp"

# Create the readers
artifacts = Artifacts()
grid_reader = GridReader(artifacts)
episode_reader = EpisodeReader(artifacts, StateReader())

# List all episodes in the grid
episodes = grid_reader.list_episodes(version, split_name)
print(f"Episodes on disk: {len(episodes)}")

# Extract every episode and collect stats
start_time = time.time()
stats = []
mismatches = []
for i, params in enumerate(episodes):
    extract = episode_reader.read(params)
    stats.append({
        "model_name": params.model_name,
        "agent_name": params.agent_name,
        "eval_name": params.eval_name,
        "episode": params.episode_id,
        "success": extract.state.task_state.success,
        "history_steps": len(extract.state.step_history),
        "details_steps": len(extract.details),
        "env_diffs": len(extract.env_diffs()),
        "message_steps": len(extract.last_messages),
        "message_files": sum(len(m) for m in extract.last_messages.values()),
        "plan_chars": len(extract.state.plan),
        "memory_keys": len(extract.state.memories),
    })
    # Invariant: step_history has one extra terminal entry (final env state, no agent action)
    if len(extract.state.step_history) != len(extract.details) + 1:
        mismatches.append(f"{params.model_name}/{params.agent_name}/{params.eval_name}/episode-{params.episode_id}: "
                          f"history={len(extract.state.step_history)} details={len(extract.details)}")
    if (i + 1) % 200 == 0:
        print(f"Extracted {i + 1}/{len(episodes)}")
stats = pd.DataFrame(stats)
elapsed = time.time() - start_time
print(f"Extracted {len(episodes)} episodes in {elapsed:.1f}s")

# Read all results rows across the grid
eval_params = {(p.model_name, p.agent_name, p.eval_name): p for p in episodes}
results = pd.concat([grid_reader.read_results(p) for p in eval_params.values()], ignore_index=True)
print(f"Results rows: {len(results)}")

# Verify the failure population (success == False, no non-empty errors)
# Pre-registered population = react-kn + modular-full only (spec: 259 failures)
failures = results[results["success"] == False]
population = failures[failures["agent_name"].isin(["react-kn", "modular-full"])]
errors = results[results["error"] != ""]
failure_counts = failures.groupby("agent_name").size()
print(f"Failures (all agents): {len(failures)} ({failure_counts.to_dict()})")
print(f"Failure population (react-kn + modular-full): {len(population)}")
print(f"Non-empty errors: {len(errors)}")

# Verify state.yaml success agrees with results.csv success
merged = results.merge(stats, on=["model_name", "agent_name", "eval_name", "episode"], suffixes=("_results", "_state"))
disagreements = merged[merged["success_results"] != merged["success_state"]]
print(f"Results/state success disagreements: {len(disagreements)}")

# Save the failure population for downstream phases
os.makedirs(output_folder, exist_ok=True)
failure_columns = ["version", "split_name", "model_name", "agent_name", "eval_name", "episode",
                   "success", "score", "max_score", "steps", "max_steps", "max_steps_hit", "error"]
population[failure_columns].to_csv(f"{output_folder}/failures.csv", index=False)

# Save the verification report
report = [
    f"Extraction verification — {version}/{split_name} — {pd.Timestamp.now():%Y-%m-%d %H:%M}",
    f"Episodes on disk: {len(episodes)}",
    f"Episodes extracted clean: {len(stats)} in {elapsed:.1f}s",
    f"Results rows: {len(results)}",
    f"Failures (success == False, all agents): {len(failures)}",
    f"Failures by agent: {failure_counts.to_dict()}",
    f"Failure population (react-kn + modular-full): {len(population)}",
    f"Non-empty errors: {len(errors)}",
    f"Results/state success disagreements: {len(disagreements)}",
    f"Step-count anomalies (history != details + 1): {len(mismatches)}",
    *[f"  {m}" for m in mismatches],
    "",
    "Episodes per model x agent:",
    stats.groupby(["model_name", "agent_name"]).size().to_string(),
]
with open(f"{output_folder}/extraction-report.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(report) + "\n")
print(f"Report written to {output_folder}/extraction-report.txt")
