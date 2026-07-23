import os
import time
import numpy as np
import pandas as pd
from artifacts.artifacts import Artifacts
from states.reader.state_reader import StateReader
from interp.bootstrap import micro_rate_ci
from interp.grid_reader import GridReader
from interp.plan.action_matcher import ActionMatcher
from interp.plan.plan_parser import PlanParser
from interp.plan.plan_scorer import PlanScorer
from interp.plan.solution_reader import SolutionReader

# Parameters
version = "v6.0"
split_name = "test"
agent_name = "modular-full"
output_folder = "../data/interp"
bootstrap_samples = 2000
bootstrap_seed = 0

def summarize(rows, model_name, eval_family, rng):
    matched = rows["n_current_exact"] + rows["n_current_fuzzy"]
    open_steps = rows["n_steps"] - rows["n_no_open"] - rows["n_no_plan"] - rows["n_unparseable"]
    agreement = micro_rate_ci(matched, rows["n_steps"], rng, bootstrap_samples)
    agreement_open = micro_rate_ci(matched, open_steps, rng, bootstrap_samples)
    agreement_any = micro_rate_ci(matched + rows["n_any_open"], rows["n_steps"], rng, bootstrap_samples)
    recall_final = micro_rate_ci(rows["final_lcs"], rows["n_solution"], rng, bootstrap_samples)
    precision_final = micro_rate_ci(rows["final_lcs"], rows["final_n_leaves"], rng, bootstrap_samples)
    recall_step = micro_rate_ci(rows["step_lcs_sum"], rows["step_solution_sum"], rng, bootstrap_samples)
    return {"model_name": model_name, "eval_family": eval_family, "episodes": len(rows),
            "steps": rows["n_steps"].sum(), "mismatches": rows["n_mismatch"].sum(),
            "no_open": rows["n_no_open"].sum(), "no_plan": rows["n_no_plan"].sum(),
            "unparseable": rows["n_unparseable"].sum(),
            "agreement": agreement[0], "agreement_low": agreement[1], "agreement_high": agreement[2],
            "agreement_open": agreement_open[0], "agreement_open_low": agreement_open[1], "agreement_open_high": agreement_open[2],
            "agreement_any": agreement_any[0], "agreement_any_low": agreement_any[1], "agreement_any_high": agreement_any[2],
            "correct_recall_final": recall_final[0], "correct_recall_final_low": recall_final[1], "correct_recall_final_high": recall_final[2],
            "correct_precision_final": precision_final[0], "correct_precision_final_low": precision_final[1], "correct_precision_final_high": precision_final[2],
            "correct_recall_step": recall_step[0], "correct_recall_step_low": recall_step[1], "correct_recall_step_high": recall_step[2],
            "invalid_lines": rows["n_invalid_lines"].sum(), "duplicate_leaves": rows["n_duplicate_leaves"].sum(),
            "max_leaf_run": rows["max_leaf_run"].max()}

# Create the readers and scorer
artifacts = Artifacts()
state_reader = StateReader()
grid_reader = GridReader(artifacts)
solution_reader = SolutionReader()
scorer = PlanScorer(PlanParser(), ActionMatcher())

# List the episodes to score
episodes = [p for p in grid_reader.list_episodes(version, split_name) if p.agent_name == agent_name]
print(f"Episodes to score: {len(episodes)}")

# Score every episode
start_time = time.time()
rows = []
audit_rows = []
solutions = {}
for i, params in enumerate(episodes):
    folder_path = artifacts.get_episode_folder_path(params)
    state = state_reader.read(f"{folder_path}/{artifacts.get_file_name(params, 'state.yaml')}")

    # Read the ground-truth solution (cached per eval x episode)
    solution_key = (params.eval_name, params.episode_id)
    if solution_key not in solutions:
        solutions[solution_key] = solution_reader.read(split_name, params.eval_name, params.episode_id)
    solution = solutions[solution_key]

    # Score plan-action agreement over the acted-on steps (the last history entry is terminal)
    steps = [(step.agent_state.plan, step.agent_state.action) for step in state.step_history[:-1]]
    agreement = scorer.score_agreement(steps)

    # Score plan correctness on the final plan and averaged over the per-step plans
    final = scorer.score_correctness(state.plan, solution)
    step_lcs_sum = step_solution_sum = 0
    for plan_text, _ in steps:
        if plan_text.strip():
            step_lcs_sum += scorer.score_correctness(plan_text, solution)["lcs"]
            step_solution_sum += len(solution)

    hygiene = scorer.score_hygiene(state.plan)

    eval_family = "-".join(params.eval_name.split("-")[:2])
    rows.append({"model_name": params.model_name, "eval_name": params.eval_name, "eval_family": eval_family,
                 "episode": params.episode_id, "success": state.task_state.success,
                 **{key: value for key, value in agreement.items() if key != "mismatches"},
                 "final_lcs": final["lcs"], "final_n_leaves": final["n_leaves"], "n_solution": final["n_solution"],
                 "step_lcs_sum": step_lcs_sum, "step_solution_sum": step_solution_sum,
                 **hygiene})
    for action, leaf in agreement["mismatches"]:
        # Truncate: a pathological module can dump megabytes of prose into an action or plan item
        audit_rows.append({"model_name": params.model_name, "eval_name": params.eval_name,
                           "episode": params.episode_id, "action": " ".join(action.split())[:200],
                           "current_open_leaf": " ".join(leaf.split())[:200]})
    if (i + 1) % 100 == 0:
        print(f"Scored {i + 1}/{len(episodes)}")
rows = pd.DataFrame(rows)
elapsed = time.time() - start_time
print(f"Scored {len(rows)} episodes in {elapsed:.1f}s")

# Save the per-episode scores and the mismatch audit table
os.makedirs(output_folder, exist_ok=True)
rows.to_csv(f"{output_folder}/plan-faithfulness.csv", index=False)
pd.DataFrame(audit_rows).to_csv(f"{output_folder}/plan-faithfulness-audit.csv", index=False)

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
summaries.to_csv(f"{output_folder}/plan-faithfulness-summary.csv", index=False)

# Save the report
overall = summaries.iloc[-1]
report = [
    f"Plan faithfulness (metric 3) — {version}/{split_name}/{agent_name} — {pd.Timestamp.now():%Y-%m-%d %H:%M}",
    f"Episodes scored: {len(rows)} in {elapsed:.1f}s",
    "",
    f"Steps scored: {overall['steps']} (mismatches {overall['mismatches']}, plan-complete {overall['no_open']}, no-plan {overall['no_plan']}, unparseable {overall['unparseable']})",
    f"Plan-action agreement (headline): {overall['agreement']:.4f} [{overall['agreement_low']:.4f}, {overall['agreement_high']:.4f}] over all steps",
    f"  conditional on an open item:    {overall['agreement_open']:.4f} [{overall['agreement_open_low']:.4f}, {overall['agreement_open_high']:.4f}]",
    f"  any-open-item (loose):          {overall['agreement_any']:.4f} [{overall['agreement_any_low']:.4f}, {overall['agreement_any_high']:.4f}]",
    "",
    f"Plan correctness, final plan vs solution (LCS): recall {overall['correct_recall_final']:.4f} [{overall['correct_recall_final_low']:.4f}, {overall['correct_recall_final_high']:.4f}], precision {overall['correct_precision_final']:.4f} [{overall['correct_precision_final_low']:.4f}, {overall['correct_precision_final_high']:.4f}]",
    f"Plan correctness, per-step mean (LCS recall):   {overall['correct_recall_step']:.4f} [{overall['correct_recall_step_low']:.4f}, {overall['correct_recall_step_high']:.4f}]",
    "",
    f"Hygiene: invalid lines {overall['invalid_lines']}, duplicate leaves {overall['duplicate_leaves']}, max identical-leaf run {overall['max_leaf_run']}",
    "",
    "Per model (all eval families):",
    summaries[summaries["eval_family"] == "all"].to_string(index=False),
    "",
    "Per eval family (all models):",
    summaries[summaries["model_name"] == "all"].to_string(index=False),
]
with open(f"{output_folder}/plan-faithfulness-report.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(report) + "\n")
print(f"Report written to {output_folder}/plan-faithfulness-report.txt")
