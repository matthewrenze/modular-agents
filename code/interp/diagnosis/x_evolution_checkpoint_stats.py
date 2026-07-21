import glob
import json
from collections import Counter
import pandas as pd

# Scratch: D2 evolution-condition checkpoint stats — accuracy vs C2 ground truth on the
# 5 modular checkpoint episodes, token/cost actuals, and the refined full-sweep forecast.

# Ground truth = C2 majority labels (same construction as x_judge_accuracy.py)
gt = {}
for path in glob.glob("../data/interp/diagnosis/labeler/*/*.json"):
    d = json.load(open(path))
    if d.get("record"):
        key = f"{d['model_name']}--{d['agent_name']}--{d['eval_name']}--episode-{d['episode']}"
        gt.setdefault(key, []).append(d["record"]["primary_cause"])
majority = {k: Counter(v).most_common(1)[0][0] for k, v in gt.items()
            if Counter(v).most_common(1)[0][1] >= 2}

rows = []
for path in sorted(glob.glob("../data/interp/diagnosis/judge/evolution/*/*.json")):
    d = json.load(open(path))
    key = f"{d['model_name']}--{d['agent_name']}--{d['eval_name']}--episode-{d['episode']}"
    record = d["record"]
    rows.append({"judge": d["judge"], "key": key, "malformed": record is None,
                 "pred": record and record["primary_cause"], "gt": majority.get(key),
                 "strict": bool(record) and record["primary_cause"] == majority.get(key),
                 "in_tok": d["tokens"]["cached"] + d["tokens"]["input"],
                 "out_tok": d["tokens"]["reasoning"] + d["tokens"]["output"], "cost": d["cost"]})
df = pd.DataFrame(rows)
print(df[["judge", "key", "pred", "gt", "strict", "cost"]].to_string(index=False))
print()

# Pure-condition comparison on the same episode x judge cells
pure_correct = 0
for row in df.to_dict("records"):
    d = json.load(open(f"../data/interp/diagnosis/judge/pure/{row['judge']}/{row['key']}.json"))
    pure_correct += bool(d["record"]) and d["record"]["primary_cause"] == majority.get(row["key"])
print(f"malformed: {df.malformed.sum()} | strict: evolution {df.strict.sum()}/{len(df)} vs pure {pure_correct}/{len(df)} (same cells)")
print(f"mean input tok: {df.in_tok.mean():,.0f} | mean output tok: {df.out_tok.mean():,.0f}")
print(f"checkpoint cost: ${df.cost.sum():.2f}")

# Forecast: scale input by full-population bundle chars; hold per-call output at checkpoint mean
sizes = pd.read_csv("../data/interp/diagnosis/evolution-bundle-sizes.csv")
scale = sizes.evolution_chars.sum() / sizes[sizes.key.isin(set(df.key))].evolution_chars.sum()
prices = {"gpt-5.6-sol": (5.0, 30.0), "claude-fable-5": (10.0, 50.0), "gemini-3.1-pro-preview": (2.0, 12.0)}
total = 0.0
for judge, group in df.groupby("judge"):
    in_price, out_price = prices[judge]
    est_in, est_out = group.in_tok.sum() * scale, group.out_tok.mean() * len(sizes)
    est = est_in / 1e6 * in_price + est_out / 1e6 * out_price
    total += est
    print(f"{judge}: forecast ${est:.0f} (input {est_in / 1e6:.1f}M, output {est_out / 1e6:.2f}M)")
print(f"FULL-SWEEP FORECAST: ${total:.0f} for 126 episodes x 3 judges (${df.cost.sum():.2f} of it already spent)")
