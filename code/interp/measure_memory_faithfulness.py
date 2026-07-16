import os
import time
import numpy as np
import pandas as pd
from artifacts.artifacts import Artifacts
from states.reader.state_reader import StateReader
from interp.episode_extract import EpisodeExtract
from interp.game_truth_reader import GameTruthReader
from interp.grid_reader import GridReader
from interp.memory_fact_parser import MemoryFactParser
from interp.memory_scorer import MemoryScorer

# Parameters
version = "v6.0"
split_name = "test"
agent_name = "modular-full"
output_folder = "../data/interp"
bootstrap_samples = 2000
bootstrap_seed = 0

def micro_rate_ci(numerators, denominators, rng):
    # Micro-averaged rate with a clustered bootstrap CI (episodes resampled with replacement)
    numerators, denominators = np.asarray(numerators), np.asarray(denominators)
    total = denominators.sum()
    if total == 0:
        return np.nan, np.nan, np.nan
    rate = numerators.sum() / total
    resampled = []
    for _ in range(bootstrap_samples):
        index = rng.integers(0, len(numerators), len(numerators))
        denominator = denominators[index].sum()
        if denominator:
            resampled.append(numerators[index].sum() / denominator)
    low, high = np.percentile(resampled, [2.5, 97.5])
    return rate, low, high

def summarize(rows, model_name, eval_family, rng):
    link_claims = rows["link_tp"] + rows["link_fp"]
    obj_claims = rows["obj_tp"] + rows["obj_fp"]
    link_precision = micro_rate_ci(rows["link_tp"], link_claims, rng)
    link_recall = micro_rate_ci(rows["traversed_hits"], rows["traversed_total"], rng)
    obj_precision = micro_rate_ci(rows["obj_tp"], obj_claims, rng)
    return {"model_name": model_name, "eval_family": eval_family, "episodes": len(rows),
            "link_claims": link_claims.sum(), "link_unresolved": rows["link_unresolved"].sum(),
            "link_precision": link_precision[0], "link_precision_low": link_precision[1], "link_precision_high": link_precision[2],
            "traversed_total": rows["traversed_total"].sum(),
            "link_recall": link_recall[0], "link_recall_low": link_recall[1], "link_recall_high": link_recall[2],
            "obj_claims": obj_claims.sum(), "obj_moved": rows["obj_moved"].sum(), "obj_unresolved": rows["obj_unresolved"].sum(),
            "obj_precision": obj_precision[0], "obj_precision_low": obj_precision[1], "obj_precision_high": obj_precision[2]}

# Create the readers, parser, and scorer
artifacts = Artifacts()
state_reader = StateReader()
grid_reader = GridReader(artifacts)
truth_reader = GameTruthReader()
parser = MemoryFactParser()
scorer = MemoryScorer()

# List the episodes to score
episodes = [p for p in grid_reader.list_episodes(version, split_name) if p.agent_name == agent_name]
print(f"Episodes to score: {len(episodes)}")

# Score every episode
start_time = time.time()
rows = []
audit_rows = []
truths = {}
for i, params in enumerate(episodes):
    folder_path = artifacts.get_episode_folder_path(params)
    state = state_reader.read(f"{folder_path}/{artifacts.get_file_name(params, 'state.yaml')}")
    details = pd.read_csv(f"{folder_path}/{artifacts.get_file_name(params, 'details.csv')}", keep_default_na=False)
    extract = EpisodeExtract(params=params, state=state, details=details)

    # Read the game ground truth (cached per eval x episode)
    truth_key = (params.eval_name, params.episode_id)
    if truth_key not in truths:
        truths[truth_key] = truth_reader.read(split_name, params.eval_name, params.episode_id)
    truth = truths[truth_key]

    # Parse the final memories and score them
    facts = parser.parse(state.memories)
    scores = scorer.score(facts, truth, extract.traversed_links(), list(details["inventory"]))

    eval_family = "-".join(params.eval_name.split("-")[:2])
    rows.append({"model_name": params.model_name, "eval_name": params.eval_name, "eval_family": eval_family,
                 "episode": params.episode_id, "success": state.task_state.success,
                 "n_memories": len(state.memories), "n_room_links": len(facts.room_links),
                 "n_unknown_links": facts.unknown_links, "n_object_locations": len(facts.object_locations),
                 "n_residue": len(facts.residue),
                 **{key: value for key, value in scores.items() if not key.startswith("fp_")}})
    for room, direction, destination, true_destination in scores["fp_links"]:
        audit_rows.append({"type": "link", "model_name": params.model_name, "eval_name": params.eval_name,
                           "episode": params.episode_id, "subject": room, "direction": direction,
                           "claimed": destination, "truth": true_destination})
    for object_name, room, true_room in scores["fp_objects"]:
        audit_rows.append({"type": "object", "model_name": params.model_name, "eval_name": params.eval_name,
                           "episode": params.episode_id, "subject": object_name, "direction": "",
                           "claimed": room, "truth": true_room})
    if (i + 1) % 100 == 0:
        print(f"Scored {i + 1}/{len(episodes)}")
rows = pd.DataFrame(rows)
elapsed = time.time() - start_time
print(f"Scored {len(rows)} episodes in {elapsed:.1f}s")

# Save the per-episode scores and the false-positive audit table
os.makedirs(output_folder, exist_ok=True)
rows.to_csv(f"{output_folder}/memory-faithfulness.csv", index=False)
pd.DataFrame(audit_rows).to_csv(f"{output_folder}/memory-faithfulness-audit.csv", index=False)

# Aggregate per model x eval family, plus marginals
rng = np.random.default_rng(bootstrap_seed)
summaries = []
for (model_name, eval_family), cell in rows.groupby(["model_name", "eval_family"]):
    summaries.append(summarize(cell, model_name, eval_family, rng))
for model_name, cell in rows.groupby("model_name"):
    summaries.append(summarize(cell, model_name, "all", rng))
for eval_family, cell in rows.groupby("eval_family"):
    summaries.append(summarize(cell, "all", eval_family, rng))
summaries.append(summarize(rows, "all", "all", rng))
summaries = pd.DataFrame(summaries)
summaries.to_csv(f"{output_folder}/memory-faithfulness-summary.csv", index=False)

# Save the report
overall = summaries.iloc[-1]
composition_columns = ["n_memories", "n_room_links", "n_unknown_links", "n_object_locations", "n_residue"]
report = [
    f"Memory faithfulness (metric 2) — {version}/{split_name}/{agent_name} — {pd.Timestamp.now():%Y-%m-%d %H:%M}",
    f"Episodes scored: {len(rows)} in {elapsed:.1f}s",
    "",
    "Memory composition (totals):",
    rows[composition_columns].sum().to_string(),
    "",
    f"Room-link precision: {overall['link_precision']:.4f} [{overall['link_precision_low']:.4f}, {overall['link_precision_high']:.4f}] over {overall['link_claims']} claims ({overall['link_unresolved']} unresolved)",
    f"Room-link recall:    {overall['link_recall']:.4f} [{overall['link_recall_low']:.4f}, {overall['link_recall_high']:.4f}] over {overall['traversed_total']} traversed links",
    f"Object precision:    {overall['obj_precision']:.4f} [{overall['obj_precision_low']:.4f}, {overall['obj_precision_high']:.4f}] over {overall['obj_claims']} claims ({overall['obj_moved']} moved excluded, {overall['obj_unresolved']} unresolved)",
    "",
    "Per model (all eval families):",
    summaries[summaries["eval_family"] == "all"].to_string(index=False),
    "",
    "Per eval family (all models):",
    summaries[summaries["model_name"] == "all"].to_string(index=False),
]
with open(f"{output_folder}/memory-faithfulness-report.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(report) + "\n")
print(f"Report written to {output_folder}/memory-faithfulness-report.txt")
