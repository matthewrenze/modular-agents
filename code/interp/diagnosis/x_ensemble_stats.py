import json
from collections import Counter
import pandas as pd

# Scratch report for task 3.1 close-out: ensemble agreement + token/cost over the Phase C records
labeler_names = ["gpt-5.6-sol", "claude-fable-5", "gemini-3.1-pro-preview"]
failures_path = "../data/interp/failures.csv"
labeler_folder = "../data/interp/diagnosis/labeler"

failures = pd.read_csv(failures_path)
print(f"Episodes: {len(failures)}")

# Load all records
records = {}  # (key, labeler) -> output dict
for row in failures.to_dict("records"):
    key = f"{row['model_name']}--{row['agent_name']}--{row['eval_name']}--episode-{row['episode']}"
    for labeler in labeler_names:
        with open(f"{labeler_folder}/{labeler}/{key}.json", "r", encoding="utf-8") as f:
            records[(key, labeler)] = json.load(f)

# Validity + token/cost per labeler
print("\n=== Per-labeler validity, tokens, cost (all 259 episodes incl. checkpoint) ===")
for labeler in labeler_names:
    outs = [records[(k, labeler)] for k in
            (f"{r['model_name']}--{r['agent_name']}--{r['eval_name']}--episode-{r['episode']}"
             for r in failures.to_dict("records"))]
    n_valid = sum(1 for o in outs if o["record"] is not None)
    n_wrong_version = sum(1 for o in outs if o["prompt_version"] != "C1")
    n_retries = sum(1 for o in outs if o["raw_retry_response"] is not None)
    tok_in = sum(o["tokens"]["cached"] + o["tokens"]["input"] for o in outs)
    tok_out = sum(o["tokens"]["reasoning"] + o["tokens"]["output"] for o in outs)
    cost = sum(o["cost"] for o in outs)
    confs = [o["record"]["confidence"] for o in outs if o["record"] and o["record"]["confidence"] is not None]
    print(f"{labeler}: valid {n_valid}/259, wrong-version {n_wrong_version}, re-asks {n_retries}, "
          f"input {tok_in:,} tok, output {tok_out:,} tok, cost ${cost:.2f}, "
          f"mean confidence {sum(confs)/len(confs):.3f} (n={len(confs)})")

# Ensemble agreement on primary_cause
print("\n=== Primary-cause ensemble agreement ===")
agreement_rows = []
for row in failures.to_dict("records"):
    key = f"{row['model_name']}--{row['agent_name']}--{row['eval_name']}--episode-{row['episode']}"
    causes = [records[(key, l)]["record"]["primary_cause"] for l in labeler_names]
    steps = [records[(key, l)]["record"]["root_cause_step"] for l in labeler_names]
    modules = [records[(key, l)]["record"]["faulty_module"] for l in labeler_names]
    counts = Counter(causes)
    top, top_n = counts.most_common(1)[0]
    level = "unanimous" if top_n == 3 else ("majority" if top_n == 2 else "none")
    step_counts = Counter(s for s in steps)
    step_top, step_top_n = step_counts.most_common(1)[0]
    step_majority = step_top if step_top_n >= 2 else "NONE"
    mod_counts = Counter(m for m in modules if m is not None)
    mod_majority = None
    if row["agent_name"] == "modular-full" and mod_counts:
        m_top, m_top_n = mod_counts.most_common(1)[0]
        mod_majority = m_top if m_top_n >= 2 else "NONE"
    agreement_rows.append({"key": key, "agent_name": row["agent_name"], "model_name": row["model_name"],
                           "eval_name": row["eval_name"], "level": level,
                           "gt": top if top_n >= 2 else None, "causes": causes,
                           "step_majority": step_majority, "module_majority": mod_majority})
adf = pd.DataFrame(agreement_rows)
for agent in ["modular-full", "react-kn"]:
    sub = adf[adf.agent_name == agent]
    lc = sub.level.value_counts()
    print(f"{agent} (n={len(sub)}): unanimous {lc.get('unanimous', 0)}, "
          f"2-of-3 {lc.get('majority', 0)}, no-majority {lc.get('none', 0)}")
lc = adf.level.value_counts()
print(f"TOTAL (n={len(adf)}): unanimous {lc.get('unanimous', 0)}, 2-of-3 {lc.get('majority', 0)}, "
      f"no-majority {lc.get('none', 0)}")

print("\n=== Ground-truth (majority) class distribution ===")
gt = adf[adf["gt"].notna()]
dist = gt.groupby(["gt", "agent_name"]).size().unstack(fill_value=0)
print(dist.to_string())
print(f"\n'other' ground truth: {len(gt[gt['gt'] == 'other'])}")

print("\n=== No-majority episodes (for task 3.2) ===")
for r in adf[adf.level == "none"].to_dict("records"):
    print(f"  {r['key']}: {r['causes']}")

print("\n=== Root-cause-step majority (exact match, incl. null) ===")
for agent in ["modular-full", "react-kn"]:
    sub = adf[adf.agent_name == agent]
    n_step = len(sub[sub.step_majority != "NONE"])
    print(f"{agent}: step majority on {n_step}/{len(sub)}")

print("\n=== Faulty-module majority (modular only) ===")
mod = adf[adf.agent_name == "modular-full"]
mc = mod.module_majority.value_counts(dropna=False)
print(mc.to_string())
