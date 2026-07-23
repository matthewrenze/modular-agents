import os
import time
import numpy as np
import pandas as pd
from artifacts.artifacts import Artifacts
from interp.bootstrap import micro_rate_ci
from interp.episode_extract import EpisodeExtract
from interp.grid_reader import GridReader
from interp.plan.action_matcher import ActionMatcher
from interp.summary.summary_parser import SummaryParser
from interp.summary.summary_scorer import SummaryScorer

# Parameters
version = "v6.0"
split_name = "test"
agent_name = "modular-full"
output_folder = "../data/interp"
bootstrap_samples = 2000
bootstrap_seed = 0

def summarize(rows, model_name, eval_family, rng):
    echo_hits = rows["echo_exact"] + rows["echo_fuzzy"]
    claim_hits = rows["loc_tp"] + rows["inv_tp"] + rows["score_tp"]
    claims = claim_hits + rows["loc_fp"] + rows["inv_fp"] + rows["score_fp"]
    change_hits = rows["loc_hits"] + rows["inv_hits"] + rows["score_hits"]
    changes = rows["loc_changes"] + rows["inv_changes"] + rows["score_changes"]
    echo_accuracy = micro_rate_ci(echo_hits, rows["n_steps"], rng, bootstrap_samples)
    precision = micro_rate_ci(claim_hits, claims, rng, bootstrap_samples)
    recall = micro_rate_ci(change_hits, changes, rng, bootstrap_samples)
    rate = lambda tp, total: tp.sum() / total.sum() if total.sum() else np.nan
    return {"model_name": model_name, "eval_family": eval_family, "episodes": len(rows),
            "steps": rows["n_steps"].sum(), "unparseable": rows["n_unparseable"].sum(),
            "echo_accuracy": echo_accuracy[0], "echo_accuracy_low": echo_accuracy[1], "echo_accuracy_high": echo_accuracy[2],
            "claims": claims.sum(),
            "precision": precision[0], "precision_low": precision[1], "precision_high": precision[2],
            "changes": changes.sum(),
            "recall": recall[0], "recall_low": recall[1], "recall_high": recall[2],
            "loc_precision": rate(rows["loc_tp"], rows["loc_tp"] + rows["loc_fp"]),
            "loc_recall": rate(rows["loc_hits"], rows["loc_changes"]),
            "inv_precision": rate(rows["inv_tp"], rows["inv_tp"] + rows["inv_fp"]),
            "inv_recall": rate(rows["inv_hits"], rows["inv_changes"]),
            "inv_recall_excl_meal": rate(rows["inv_hits"] - rows["inv_meal_hits"],
                                         rows["inv_changes"] - rows["inv_meal_changes"]),
            "score_precision": rate(rows["score_tp"], rows["score_tp"] + rows["score_fp"]),
            "score_recall": rate(rows["score_hits"], rows["score_changes"])}

# Create the readers, parser, and scorer
artifacts = Artifacts()
grid_reader = GridReader(artifacts)
scorer = SummaryScorer(SummaryParser(), ActionMatcher())

# List the episodes to score
episodes = [p for p in grid_reader.list_episodes(version, split_name) if p.agent_name == agent_name]
print(f"Episodes to score: {len(episodes)}")

# Score every episode
start_time = time.time()
rows = []
audit_rows = []
results = {}
for i, params in enumerate(episodes):
    folder_path = artifacts.get_episode_folder_path(params)
    details = pd.read_csv(f"{folder_path}/{artifacts.get_file_name(params, 'details.csv')}", keep_default_na=False)
    extract = EpisodeExtract(params=params, state=None, details=details)

    # Read the episode outcome (cached per model x eval)
    results_key = (params.model_name, params.eval_name)
    if results_key not in results:
        results[results_key] = grid_reader.read_results(params).set_index("episode")
    success = results[results_key].loc[params.episode_id, "success"]

    # Score the summaries against the env diffs
    steps = list(zip(details["summary"], extract.env_diffs()))
    scores = scorer.score(steps)

    eval_family = "-".join(params.eval_name.split("-")[:2])
    rows.append({"model_name": params.model_name, "eval_name": params.eval_name, "eval_family": eval_family,
                 "episode": params.episode_id, "success": success,
                 **{key: value for key, value in scores.items() if not isinstance(value, list)}})
    clip = lambda text: str(text)[:150]  # raw actions can be multi-KB model dumps
    for kind, claimed, truth in scores["fp_claims"]:
        audit_rows.append({"type": f"fp_{kind}", "model_name": params.model_name, "eval_name": params.eval_name,
                           "episode": params.episode_id, "claimed": clip(claimed), "truth": clip(truth)})
    for kind, truth in scores["missed_changes"]:
        audit_rows.append({"type": f"missed_{kind}", "model_name": params.model_name, "eval_name": params.eval_name,
                           "episode": params.episode_id, "claimed": "", "truth": clip(truth)})
    for echo, expected in scores["echo_mismatches"]:
        audit_rows.append({"type": "echo_mismatch", "model_name": params.model_name, "eval_name": params.eval_name,
                           "episode": params.episode_id, "claimed": clip(echo), "truth": clip(expected)})
    if (i + 1) % 100 == 0:
        print(f"Scored {i + 1}/{len(episodes)}")
rows = pd.DataFrame(rows)
elapsed = time.time() - start_time
print(f"Scored {len(rows)} episodes in {elapsed:.1f}s")

# Save the per-episode scores and the audit table
os.makedirs(output_folder, exist_ok=True)
rows.to_csv(f"{output_folder}/summary-fidelity.csv", index=False)
pd.DataFrame(audit_rows).to_csv(f"{output_folder}/summary-fidelity-audit.csv", index=False)

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
summaries.to_csv(f"{output_folder}/summary-fidelity-summary.csv", index=False)

# Save the report
overall = summaries.iloc[-1]
composition_columns = ["n_steps", "n_unparseable", "n_multiline", "echo_exact", "echo_fuzzy", "echo_mismatch",
                       "loc_tp", "loc_fp", "loc_redundant", "inv_tp", "inv_fp", "score_tp", "score_fp",
                       "n_obj_state", "n_failure", "n_other"]
splits = []
for outcome, cell in rows.groupby("success"):
    split = summarize(cell, "all", "all", rng)
    splits.append(f"success={outcome}: episodes={split['episodes']} echo={split['echo_accuracy']:.4f} "
                  f"precision={split['precision']:.4f} recall={split['recall']:.4f}")
report = [
    f"Summary fidelity (metric 4) — {version}/{split_name}/{agent_name} — {pd.Timestamp.now():%Y-%m-%d %H:%M}",
    f"Episodes scored: {len(rows)} in {elapsed:.1f}s",
    "",
    "Step and claim composition (totals):",
    rows[composition_columns].sum().to_string(),
    "",
    f"Action-echo accuracy: {overall['echo_accuracy']:.4f} [{overall['echo_accuracy_low']:.4f}, {overall['echo_accuracy_high']:.4f}] over {overall['steps']} steps ({overall['unparseable']} unparseable)",
    f"Claim precision:      {overall['precision']:.4f} [{overall['precision_low']:.4f}, {overall['precision_high']:.4f}] over {overall['claims']} location/inventory/score claims",
    f"Change recall:        {overall['recall']:.4f} [{overall['recall_low']:.4f}, {overall['recall_high']:.4f}] over {overall['changes']} env changes",
    f"Per channel: location P={overall['loc_precision']:.4f} R={overall['loc_recall']:.4f} | "
    f"inventory P={overall['inv_precision']:.4f} R={overall['inv_recall']:.4f} | "
    f"score P={overall['score_precision']:.4f} R={overall['score_recall']:.4f}",
    f"Inventory recall excluding meal-preparation steps (ingredient consumption exceeds the "
    f"summary's 3-outcome cap): {overall['inv_recall_excl_meal']:.4f}",
    "",
    "Failure-vs-success split:",
    *splits,
    "",
    "Per model (all eval families):",
    summaries[summaries["eval_family"] == "all"].to_string(index=False),
    "",
    "Per eval family (all models):",
    summaries[summaries["model_name"] == "all"].to_string(index=False),
]
with open(f"{output_folder}/summary-fidelity-report.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(report) + "\n")
print(f"Report written to {output_folder}/summary-fidelity-report.txt")
