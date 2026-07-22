import json
import os
import numpy as np
import pandas as pd
from artifacts.artifacts import Artifacts
from params.parameters import Parameters
from interp.bootstrap import micro_rate_ci
from interp.diagnosis.ensemble import majority, step_window, pairwise_rate, fleiss_kappa
from interp.diagnosis.scoring import (score_class, score_step, cohens_kappa, chance_floors,
                                      brier_score, reliability_bins)
from interp.diagnosis.divergence import first_divergence, corrective_matches
from interp.diagnosis.inference import fit_mixed_logistic, cell_bootstrap_diff
from interp.plan.solution_reader import SolutionReader

# Parameters
version = "v6.0"
split_name = "test"
data_folder = "../data/interp"
diagnosis_folder = "../data/interp/diagnosis"
instruments = ["gpt-5.6-sol", "claude-fable-5", "gemini-3.1-pro-preview"]
judge_conditions = ["pure", "feedback", "evolution"]  # + agentic, loaded from its own folder
architectures = ["modular-full", "react-kn"]
bootstrap_samples = 2000
bootstrap_seed = 0

def family(eval_name: str) -> str:
    return "-".join(eval_name.split("-")[:2])

def load_record(path: str):
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def rate(subset, column) -> str:
    return f"{subset[column].mean():.3f} ({subset[column].sum()}/{len(subset)})"

def episode_ci(subset, column, rng) -> str:
    # Episode-clustered bootstrap CI on a pooled per-observation rate (section 35 convention)
    cells = subset.groupby("key")[column].agg(["sum", "count"])
    value, low, high = micro_rate_ci(cells["sum"], cells["count"], rng, bootstrap_samples)
    return f"{value:.3f} [{low:.3f}, {high:.3f}] ({subset[column].sum()}/{len(subset)})"

def majority_vote_accuracy(subset, truth) -> str:
    correct = total = no_vote = 0
    for key, group in subset.groupby("key"):
        votes = [vote for vote in group.judge_primary if vote is not None]
        total += 1
        slug = majority(votes) if votes else None
        if slug is None:
            no_vote += 1
        else:
            correct += slug == truth[key]
    return f"{correct / total:.3f} ({correct}/{total}, no-vote {no_vote})"

def main():
    # Scored population = failures minus Gate 3 exclusions (decisions section 84)
    failures = pd.read_csv(f"{data_folder}/failures.csv")
    exclusions = pd.read_csv(f"{diagnosis_folder}/exclusions.csv")
    join_columns = ["model_name", "agent_name", "eval_name", "episode"]
    merged = failures.merge(exclusions[join_columns], on=join_columns, how="left", indicator=True)
    failures["key"] = (failures.model_name + "--" + failures.agent_name + "--"
                       + failures.eval_name + "--episode-" + failures.episode.astype(str))
    scored = failures[(merged["_merge"] == "left_only").values].copy()
    episode_rows = {row["key"]: row for row in scored.to_dict("records")}

    # Load the C2 labeler records (all 259 for agreement stats; scored 242 for ground truth)
    labeler_records = {key: {} for key in failures.key}
    for labeler in instruments:
        for key in failures.key:
            data = load_record(f"{diagnosis_folder}/labeler/{labeler}/{key}.json")
            labeler_records[key][labeler] = data["record"]

    # Ground truth per scored episode: class, step (+ dynamic window), module (2-of-3 majority)
    truth, truth_step, truth_window, truth_module = {}, {}, {}, {}
    for key in scored.key:
        records = [labeler_records[key][labeler] for labeler in instruments]
        truth[key] = majority([record["primary_cause"] for record in records])
        assert truth[key] is not None, f"no class majority for scored episode {key}"
        steps = [record["root_cause_step"] for record in records]
        truth_step[key] = majority(steps)
        truth_window[key] = step_window(steps)
        if "--modular-full--" in key:
            truth_module[key] = majority([record["faulty_module"] for record in records])

    # Mechanical first-divergence anchor + corrective-action ground truth (tw-coin only)
    artifacts, solution_reader = Artifacts(), SolutionReader()
    solutions = {}
    mechanical = {}
    for row in scored.to_dict("records"):
        if family(row["eval_name"]) != "tw-coin":
            continue
        params = Parameters(version=version, split_name=split_name, model_name=row["model_name"],
                            agent_name=row["agent_name"], eval_name=row["eval_name"],
                            episode_id=row["episode"])
        details_path = (f"{artifacts.get_episode_folder_path(params)}/"
                        f"{artifacts.get_file_name(params, 'details.csv')}")
        details = pd.read_csv(details_path, keep_default_na=False)
        solution_key = (row["eval_name"], row["episode"])
        if solution_key not in solutions:
            solutions[solution_key] = solution_reader.read(split_name, row["eval_name"], row["episode"])
        mechanical[row["key"]] = first_divergence(list(details["action"]), solutions[solution_key])

    # Assemble the long observation table: 3 judges x 4 conditions x scored episodes
    rows = []
    for judge in instruments:
        for condition in judge_conditions + ["agentic"]:
            base = (f"{diagnosis_folder}/agentic-judge/{judge}" if condition == "agentic"
                    else f"{diagnosis_folder}/judge/{condition}/{judge}")
            for key, episode_row in episode_rows.items():
                data = load_record(f"{base}/{key}.json")
                if data is None:
                    continue
                record = data["record"]
                divergence = mechanical.get(key)
                row = {"judge": judge, "condition": condition, "key": key,
                       "model_name": episode_row["model_name"], "agent_name": episode_row["agent_name"],
                       "eval_name": episode_row["eval_name"], "eval_family": family(episode_row["eval_name"]),
                       "episode": episode_row["episode"], "ground_truth": truth[key],
                       "gt_step": truth_step[key], "gt_module": truth_module.get(key),
                       "valid": record is not None,
                       "judge_primary": record["primary_cause"] if record else None,
                       "judge_secondary": record["secondary_cause"] if record else None,
                       "root_cause_step": record["root_cause_step"] if record else None,
                       "faulty_module": record["faulty_module"] if record else None,
                       "confidence": record["confidence"] if record else None,
                       "strict": False, "lenient": False,
                       "step_exact": False, "step_window2": False, "step_dynamic": False,
                       "has_step_gt": truth_step[key] is not None,
                       "module_correct": False, "has_module_gt": truth_module.get(key) is not None,
                       "corrective_scored": bool(record and divergence),
                       "corrective_correct": bool(record and divergence
                                                  and corrective_matches(record["corrective_action"],
                                                                         divergence[1])),
                       "bundle_chars": data.get("bundle_chars"),
                       "retrieved_chars": data.get("retrieval", {}).get("total_chars"),
                       "read_turns": data.get("read_turns"),
                       "input_tokens": data["tokens"]["cached"] + data["tokens"]["input"],
                       "output_tokens": data["tokens"].get("reasoning", 0) + data["tokens"]["output"],
                       "cost": data["cost"]}
                if record:
                    row.update(score_class(record["primary_cause"], record["secondary_cause"], truth[key]))
                    if truth_step[key] is not None:
                        row.update(score_step(record["root_cause_step"], truth_step[key], truth_window[key]))
                    if row["has_module_gt"]:
                        row["module_correct"] = record["faulty_module"] == truth_module[key]
                rows.append(row)
    observations = pd.DataFrame(rows)
    observations.to_csv(f"{diagnosis_folder}/diagnosability.csv", index=False)
    valid = observations[observations.valid]

    rng = np.random.default_rng(bootstrap_seed)
    lines = [f"Diagnosability statistics (task 4.3) — {version}/{split_name} — "
             f"{pd.Timestamp.now():%Y-%m-%d %H:%M}", ""]

    # --- Populations, coverage, exclusions
    lines.append("=== Population & coverage ===")
    lines.append(f"Failures: {len(failures)}; Gate 3 exclusions: {len(exclusions)} "
                 f"({dict(exclusions.reason.value_counts())}); scored population: {len(scored)} "
                 f"({sum(scored.agent_name == 'modular-full')} modular / "
                 f"{sum(scored.agent_name == 'react-kn')} react)")
    for condition in judge_conditions + ["agentic"]:
        subset = observations[observations.condition == condition]
        malformed = len(subset) - subset.valid.sum()
        lines.append(f"  {condition}: {len(subset)} records, {malformed} malformed/excluded-with-count")
    step_scored = sum(1 for key in scored.key if truth_step[key] is not None)
    module_scored = sum(1 for value in truth_module.values() if value is not None)
    lines.append(f"Step ground truth: {step_scored}/{len(scored)} episodes; module ground truth: "
                 f"{module_scored}/{len(truth_module)} modular episodes")
    lines.append("")

    # --- Ground truth: distribution, ensemble agreement, chance floors
    lines.append("=== Ground truth (C2 ensemble, scored population) ===")
    counts = pd.Series(truth).value_counts()
    lines.append("Class distribution: " + ", ".join(f"{slug} {count}" for slug, count in counts.items()))
    class_votes = [[labeler_records[key][labeler]["primary_cause"] for labeler in instruments]
                   for key in failures.key]
    unanimous = sum(len(set(votes)) == 1 for votes in class_votes)
    two_of_three = sum(len(set(votes)) == 2 for votes in class_votes)
    lines.append(f"Ensemble agreement (all {len(failures)} failures): unanimous {unanimous}, "
                 f"2-of-3 {two_of_three}, none {len(failures) - unanimous - two_of_three}; "
                 f"Fleiss kappa {fleiss_kappa(class_votes):.3f}")
    for i, first in enumerate(instruments):
        for second in instruments[i + 1:]:
            agreement = pairwise_rate([votes[i] for votes in class_votes],
                                      [votes[instruments.index(second)] for votes in class_votes])
            lines.append(f"  pairwise {first} vs {second}: {agreement:.3f}")
    step_votes = [[labeler_records[key][labeler]["root_cause_step"] for labeler in instruments]
                  for key in failures.key]
    step_majorities = sum(majority(votes) is not None for votes in step_votes)
    lines.append(f"Step agreement: majority on {step_majorities}/{len(failures)}; "
                 f"Fleiss kappa {fleiss_kappa(step_votes):.3f}")
    scored_truth = [truth[key] for key in scored.key]
    scored_families = [family(name) for name in scored.eval_name]
    conditional = chance_floors(scored_truth, scored_families)
    unconditional = chance_floors(scored_truth, ["all"] * len(scored_truth))
    lines.append(f"Chance floors (operative, eval-conditional): majority {conditional['majority']:.3f}, "
                 f"matched-random {conditional['matched_random']:.3f}")
    lines.append(f"Chance floors (unconditional): majority {unconditional['majority']:.3f}, "
                 f"matched-random {unconditional['matched_random']:.3f}")
    lines.append("")

    # --- Primary metric: accuracy per condition x architecture
    for condition in judge_conditions + ["agentic"]:
        subset = valid[valid.condition == condition]
        lines.append(f"=== Condition: {condition} ===")
        for architecture in architectures:
            arch_subset = subset[subset.agent_name == architecture]
            if len(arch_subset) == 0:
                continue
            lines.append(f"  {architecture}: pooled strict {episode_ci(arch_subset, 'strict', rng)}, "
                         f"lenient {rate(arch_subset, 'lenient')}")
            lines.append(f"    majority-vote {majority_vote_accuracy(arch_subset, truth)}; Cohen's kappa "
                         f"{cohens_kappa(list(arch_subset.judge_primary), list(arch_subset.ground_truth)):.3f}")
            for judge in instruments:
                judge_subset = arch_subset[arch_subset.judge == judge]
                lines.append(f"    {judge}: strict {rate(judge_subset, 'strict')}, "
                             f"lenient {rate(judge_subset, 'lenient')}")
        lines.append("  By eval family (pooled strict):")
        for (architecture, eval_family), group in subset.groupby(["agent_name", "eval_family"]):
            lines.append(f"    {architecture} / {eval_family}: {rate(group, 'strict')}")
        lines.append("  By failure mode (pooled strict):")
        for (architecture, slug), group in subset.groupby(["agent_name", "ground_truth"]):
            lines.append(f"    {architecture} / {slug}: {rate(group, 'strict')}")
        lines.append("")

    # --- Per agent model (pure + agentic), pooled strict
    lines.append("=== By agent model (pooled strict) ===")
    for condition in ["pure", "agentic"]:
        subset = valid[valid.condition == condition]
        lines.append(f"  {condition}:")
        for (architecture, model_name), group in subset.groupby(["agent_name", "model_name"]):
            lines.append(f"    {architecture} / {model_name}: {rate(group, 'strict')}")
    lines.append("")

    # --- Inference: mixed-effects logistic + clustered bootstrap per contrast
    lines.append("=== Inference (mixed-effects logistic + cell bootstrap; protocol section 11) ===")
    contrasts = {
        "pure (headline)": valid[valid.condition == "pure"],
        "feedback": valid[valid.condition == "feedback"],
        "agentic": valid[valid.condition == "agentic"],
        "trail (modular evolution vs react pure)": pd.concat([
            valid[(valid.condition == "evolution") & (valid.agent_name == "modular-full")],
            valid[(valid.condition == "pure") & (valid.agent_name == "react-kn")]])}
    for name, frame in contrasts.items():
        fit = fit_mixed_logistic(frame.rename(columns={"strict": "correct"}))
        effect = fit["fixed"]["agent_name[T.react-kn]"]
        boot = cell_bootstrap_diff(frame.rename(columns={"strict": "correct"}),
                                   bootstrap_samples, bootstrap_seed)
        mixed_significant = effect["p"] < 0.05
        boot_significant = not (boot["diff_low"] <= 0.0 <= boot["diff_high"])
        lines.append(f"  {name}:")
        lines.append(f"    mixed-effects react effect (log-odds): {effect['mean']:+.3f} "
                     f"[{effect['ci_low']:+.3f}, {effect['ci_high']:+.3f}], p = {effect['p']:.4f}")
        lines.append(f"    bootstrap: modular {boot['modular']:.3f} [{boot['modular_low']:.3f}, "
                     f"{boot['modular_high']:.3f}], react {boot['react']:.3f} [{boot['react_low']:.3f}, "
                     f"{boot['react_high']:.3f}], diff {boot['diff']:+.3f} "
                     f"[{boot['diff_low']:+.3f}, {boot['diff_high']:+.3f}]")
        agreement = "AGREE" if mixed_significant == boot_significant else "DISAGREE (flagged)"
        lines.append(f"    routes {agreement}: mixed p<0.05 = {mixed_significant}, "
                     f"bootstrap CI excludes 0 = {boot_significant}")
        lines.append(f"    [mixed-effects model summary]\n{fit['summary']}")
    lines.append("")

    # --- Secondary metric: root-cause-step localization
    lines.append("=== Root-cause-step localization (secondary; step-GT episodes only) ===")
    step_subset = valid[valid.has_step_gt]
    for condition in judge_conditions + ["agentic"]:
        for architecture in architectures:
            group = step_subset[(step_subset.condition == condition)
                                & (step_subset.agent_name == architecture)]
            if len(group) == 0:
                continue
            lines.append(f"  {condition} / {architecture}: exact {rate(group, 'step_exact')}, "
                         f"+/-2 {rate(group, 'step_window2')}, dynamic {rate(group, 'step_dynamic')}")
    lines.append("")

    # --- Exploratory: module attribution
    lines.append("=== Module attribution (exploratory; modular episodes with module GT) ===")
    module_truths = [value for value in truth_module.values() if value is not None]
    module_by_class = pd.DataFrame({"slug": [truth[key] for key, value in truth_module.items()
                                             if value is not None], "module": module_truths})
    modal_hits = sum(group.value_counts().iloc[0] for _, group in module_by_class.groupby("slug")["module"])
    lines.append(f"Class-conditional modal-module baseline: {modal_hits / len(module_truths):.3f}")
    module_subset = valid[valid.has_module_gt]
    for condition in judge_conditions + ["agentic"]:
        group = module_subset[module_subset.condition == condition]
        if len(group):
            lines.append(f"  {condition}: {rate(group, 'module_correct')}")
    lines.append("")

    # --- Exploratory: corrective action (tw-coin, mechanical) + mechanical step validation
    lines.append("=== Corrective action (exploratory; tw-coin episodes with a mechanical divergence) ===")
    corrective = valid[valid.corrective_scored]
    for condition in judge_conditions + ["agentic"]:
        for architecture in architectures:
            group = corrective[(corrective.condition == condition)
                               & (corrective.agent_name == architecture)]
            if len(group):
                lines.append(f"  {condition} / {architecture}: {rate(group, 'corrective_correct')}")
    diverged = {key: value for key, value in mechanical.items() if value is not None}
    both = [key for key in diverged if truth_step[key] is not None]
    exact = sum(truth_step[key] == diverged[key][0] for key in both)
    within = sum(abs(truth_step[key] - diverged[key][0]) <= 2 for key in both)
    lines.append(f"Mechanical divergence found: {len(diverged)}/{len(mechanical)} tw-coin episodes")
    lines.append(f"Ensemble step vs mechanical divergence ({len(both)} episodes with both): "
                 f"exact {exact}/{len(both)} = {exact / len(both):.3f}, "
                 f"+/-2 {within}/{len(both)} = {within / len(both):.3f}")
    lines.append("")

    # --- Exploratory: confidence calibration
    lines.append("=== Confidence calibration (valid records with confidence) ===")
    confident = valid[valid.confidence.notna()]
    for judge in instruments:
        for condition in judge_conditions + ["agentic"]:
            group = confident[(confident.judge == judge) & (confident.condition == condition)]
            if len(group):
                score = brier_score(list(group.confidence), list(group.strict))
                lines.append(f"  {judge} / {condition}: Brier {score:.3f}, "
                             f"mean confidence {group.confidence.mean():.3f}, accuracy {group.strict.mean():.3f}")
    for judge in instruments:
        group = confident[confident.judge == judge]
        lines.append(f"  {judge} reliability (all conditions): " + "; ".join(
            f"[{row['low']:.1f}-{row['high']:.1f}] n={row['n']} conf {row['mean_confidence']:.2f} "
            f"acc {row['accuracy']:.2f}" for row in reliability_bins(list(group.confidence),
                                                                    list(group.strict))))
    lines.append("")

    # --- Diagnostic cost: bundle/retrieval sizes and tokens
    lines.append("=== Diagnostic cost ===")
    for condition in judge_conditions:
        for architecture in architectures:
            group = observations[(observations.condition == condition)
                                 & (observations.agent_name == architecture)]
            if len(group):
                lines.append(f"  {condition} / {architecture}: mean bundle {group.bundle_chars.mean():,.0f} chars, "
                             f"mean input {group.input_tokens.mean():,.0f} tokens")
    agentic = observations[observations.condition == "agentic"]
    for architecture in architectures:
        group = agentic[agentic.agent_name == architecture]
        cells = group.groupby("key")["retrieved_chars"].agg(["sum", "count"])
        mean, low, high = micro_rate_ci(cells["sum"], cells["count"], rng, bootstrap_samples)
        lines.append(f"  agentic / {architecture}: retrieved chars mean {mean:,.0f} [{low:,.0f}, {high:,.0f}], "
                     f"median {group.retrieved_chars.median():,.0f}, "
                     f"p90 {group.retrieved_chars.quantile(0.9):,.0f}; "
                     f"read turns mean {group.read_turns.mean():.1f}; "
                     f"mean input {group.input_tokens.mean():,.0f} tokens")
    modular_chars = agentic[agentic.agent_name == "modular-full"].retrieved_chars
    react_chars = agentic[agentic.agent_name == "react-kn"].retrieved_chars
    lines.append(f"  agentic retrieval ratio (modular/react means): "
                 f"{modular_chars.mean() / react_chars.mean():.2f}x chars")
    lines.append("")

    # --- Agentic cost curves: fraction correctly diagnosed within a reading budget
    curve_rows = []
    for architecture in architectures:
        group = agentic[agentic.valid & (agentic.agent_name == architecture)]
        group = group.sort_values("retrieved_chars")
        cumulative = group.strict.cumsum()
        for rank, (chars, correct) in enumerate(zip(group.retrieved_chars, cumulative), start=1):
            curve_rows.append({"agent_name": architecture, "rank": rank, "retrieved_chars": chars,
                               "cumulative_correct": correct, "n_observations": len(group),
                               "cumulative_accuracy": correct / len(group)})
    pd.DataFrame(curve_rows).to_csv(f"{diagnosis_folder}/diagnosability-cost-curve.csv", index=False)
    lines.append(f"Cost curves written to diagnosability-cost-curve.csv "
                 f"(cumulative accuracy vs retrieval budget, per architecture)")

    report = "\n".join(lines)
    with open(f"{diagnosis_folder}/diagnosability-stats.txt", "w", encoding="utf-8") as f:
        f.write(report + "\n")
    print(report)

if __name__ == "__main__":
    main()
