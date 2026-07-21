import json
import os
from collections import Counter
import pandas as pd

JUDGES = ["gpt-5.6-sol", "claude-fable-5", "gemini-3.1-pro-preview"]
CONDITIONS = ["pure", "feedback", "evolution"]  # evolution = D2, modular-only (decisions section 99)
EVAL_FAMILY = lambda name: name.rsplit("-", 1)[0]  # tw-coin-1 -> tw-coin

def load_records(base, model, keys):
    # Missing files are tolerated (a leg may be incomplete) and reported as coverage
    records = {}
    for key in keys:
        path = f"{base}/{model}/{key}.json"
        if not os.path.exists(path):
            continue
        with open(path, "r", encoding="utf-8") as f:
            records[key] = json.load(f)
    return records

# Scored population = failures minus Gate 3 exclusions (242 episodes)
failures = pd.read_csv("../data/interp/failures.csv")
exclusions = pd.read_csv("../data/interp/diagnosis/exclusions.csv")
merged = failures.merge(exclusions[["model_name", "agent_name", "eval_name", "episode"]],
                        on=["model_name", "agent_name", "eval_name", "episode"], how="left", indicator=True)
failures = failures[(merged["_merge"] == "left_only").values].copy()
failures["key"] = (failures.model_name + "--" + failures.agent_name + "--" + failures.eval_name
                   + "--episode-" + failures.episode.astype(str))
keys = list(failures.key)
print(f"Scored population: {len(keys)}")

# Ground truth = C2 tri-labeler majority (must exist for every scored episode)
labeler_records = {m: load_records("../data/interp/diagnosis/labeler", m, keys) for m in JUDGES}
truth = {}
for key in keys:
    votes = [labeler_records[m][key]["record"]["primary_cause"] for m in JUDGES]
    slug, count = Counter(votes).most_common(1)[0]
    assert count >= 2, f"no majority for scored episode {key}"
    truth[key] = slug
print("Ground-truth classes:", dict(Counter(truth.values()).most_common()))

# Judge records -> long accuracy table
rows = []
for judge in JUDGES:
    for condition in CONDITIONS:
        judge_records = load_records(f"../data/interp/diagnosis/judge/{condition}", judge, keys)
        print(f"coverage {judge} / {condition}: {len(judge_records)}/{len(keys)}")
        for row in failures.to_dict("records"):
            if row["key"] not in judge_records:
                continue
            data = judge_records[row["key"]]
            record = data["record"]
            gt = truth[row["key"]]
            rows.append({
                "judge": judge, "condition": condition, "model_name": row["model_name"],
                "agent_name": row["agent_name"], "eval_name": row["eval_name"],
                "eval_family": EVAL_FAMILY(row["eval_name"]), "episode": row["episode"],
                "ground_truth": gt, "malformed": record is None,
                "judge_primary": record["primary_cause"] if record else None,
                "judge_secondary": record["secondary_cause"] if record else None,
                "strict": bool(record and record["primary_cause"] == gt),
                "lenient": bool(record and gt in [record["primary_cause"], record["secondary_cause"]]),
                "root_cause_step": record["root_cause_step"] if record else None,
                "faulty_module": record["faulty_module"] if record else None,
                "confidence": record["confidence"] if record else None,
                "bundle_chars": data["bundle_chars"],
                "input_tokens": data["tokens"]["cached"] + data["tokens"]["input"],
                "output_tokens": data["tokens"]["reasoning"] + data["tokens"]["output"],
                "cost": data["cost"]})
results = pd.DataFrame(rows)
results.to_csv("../data/interp/diagnosis/judge-accuracy.csv", index=False)

def rate(frame, column):
    return f"{frame[column].mean():.3f} ({frame[column].sum()}/{len(frame)})"

lines = [f"Scored population: {len(keys)} episodes x {len(JUDGES)} judges x {len(CONDITIONS)} conditions",
         f"Malformed judge records: {results.malformed.sum()}", ""]
for condition in CONDITIONS:
    lines.append(f"=== Condition: {condition} ===")
    subset = results[results.condition == condition]
    for arch in ["modular-full", "react-kn"]:
        arch_subset = subset[subset.agent_name == arch]
        if len(arch_subset) == 0:
            continue
        lines.append(f"  {arch}: pooled strict {rate(arch_subset, 'strict')}, lenient {rate(arch_subset, 'lenient')}")
        for judge in JUDGES:
            judge_subset = arch_subset[arch_subset.judge == judge]
            lines.append(f"    {judge}: strict {rate(judge_subset, 'strict')}, lenient {rate(judge_subset, 'lenient')}")
    lines.append("  By eval family (pooled strict):")
    for (arch, family), group in subset.groupby(["agent_name", "eval_family"]):
        lines.append(f"    {arch} / {family}: {rate(group, 'strict')}")
    lines.append("  By failure mode (pooled strict):")
    for (arch, gt), group in subset.groupby(["agent_name", "ground_truth"]):
        lines.append(f"    {arch} / {gt}: {rate(group, 'strict')}")
    lines.append("")

lines.append("=== Majority-vote-of-judges (variant) ===")
for condition in CONDITIONS:
    subset = results[results.condition == condition]
    for arch in ["modular-full", "react-kn"]:
        arch_subset = subset[subset.agent_name == arch]
        correct = total = 0
        for key, group in arch_subset.groupby(["model_name", "eval_name", "episode"]):
            votes = [v for v in group.judge_primary if v is not None]
            slug, count = Counter(votes).most_common(1)[0] if votes else (None, 0)
            total += 1
            correct += int(count >= 2 and slug == group.ground_truth.iloc[0])
        if total:
            lines.append(f"  {condition} / {arch}: {correct}/{total} = {correct / total:.3f}")

lines.append("")
lines.append("=== Evolution vs pure (modular, same cells; decisions section 99 prediction) ===")
modular = results[results.agent_name == "modular-full"]
pure, evolution = (modular[modular.condition == c] for c in ["pure", "evolution"])
for judge in JUDGES:
    lines.append(f"  {judge}: pure {rate(pure[pure.judge == judge], 'strict')} -> "
                 f"evolution {rate(evolution[evolution.judge == judge], 'strict')}")
lines.append(f"  pooled: pure {rate(pure, 'strict')} -> evolution {rate(evolution, 'strict')}")
lines.append("  By ground-truth class (pooled strict, pure -> evolution):")
for gt in sorted(set(evolution.ground_truth)):
    p, e = pure[pure.ground_truth == gt], evolution[evolution.ground_truth == gt]
    delta = e.strict.mean() - p.strict.mean()
    lines.append(f"    {gt}: {rate(p, 'strict')} -> {rate(e, 'strict')} (delta {delta:+.3f})")

lines.append("")
lines.append("=== Bundle sizes / tokens / cost ===")
for condition in CONDITIONS:
    subset = results[results.condition == condition]
    for arch in ["modular-full", "react-kn"]:
        arch_subset = subset[subset.agent_name == arch]
        lines.append(f"  {condition} / {arch}: mean bundle {arch_subset.bundle_chars.mean():,.0f} chars, "
                     f"mean input {arch_subset.input_tokens.mean():,.0f} tokens")
for judge in JUDGES:
    subset = results[results.judge == judge]
    lines.append(f"  {judge}: input {subset.input_tokens.sum() / 1e6:.2f}M, output {subset.output_tokens.sum() / 1e6:.2f}M, "
                 f"cost ${subset.cost.sum():.2f}")
lines.append(f"  TOTAL cost: ${results.cost.sum():.2f}")

report = "\n".join(lines)
with open("../data/interp/diagnosis/judge-accuracy-stats.txt", "w", encoding="utf-8") as f:
    f.write(report + "\n")
print(report)
