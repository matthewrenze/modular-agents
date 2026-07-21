import json
import os
from collections import Counter
import pandas as pd

JUDGES = ["gpt-5.6-sol", "claude-fable-5", "gemini-3.1-pro-preview"]
CONDITIONS = ["pure", "feedback"]
PRICES = {"gpt-5.6-sol": (5.00, 30.00), "claude-fable-5": (10.00, 50.00), "gemini-3.1-pro-preview": (2.00, 12.00)}

sizes = pd.read_csv("../data/interp/diagnosis/judge-bundle-sizes.csv")
sizes["key"] = (sizes.model_name + "--" + sizes.agent_name + "--" + sizes.eval_name
                + "--episode-" + sizes.episode.astype(str))

# Load the checkpoint judge records
records = []
for judge in JUDGES:
    for condition in CONDITIONS:
        folder = f"../data/interp/diagnosis/judge/{condition}/{judge}"
        for name in sorted(os.listdir(folder)):
            with open(f"{folder}/{name}", "r", encoding="utf-8") as f:
                data = json.load(f)
            data["key"] = name[:-5]
            records.append(data)
print(f"Records: {len(records)}; malformed: {sum(1 for r in records if r['record'] is None)}")

# Ground truth for the checkpoint episodes = C2 tri-labeler majority
keys = sorted({r["key"] for r in records})
truth = {}
for key in keys:
    votes = []
    for labeler in JUDGES:
        with open(f"../data/interp/diagnosis/labeler/{labeler}/{key}.json", "r", encoding="utf-8") as f:
            votes.append(json.load(f)["record"]["primary_cause"])
    slug, count = Counter(votes).most_common(1)[0]
    truth[key] = slug if count >= 2 else None
print("Ground truth:", {k.split("--")[2] + "/" + k.split("--")[3]: v for k, v in truth.items()})

# Per-judge accuracy, tokens, cost; input ratio vs estimated bundle tokens
rows = []
for judge in JUDGES:
    for condition in CONDITIONS:
        subset = [r for r in records if r["judge"] == judge and r["condition"] == condition]
        est_col = "pure_est_tokens" if condition == "pure" else "feedback_est_tokens"
        est = sizes.set_index("key").loc[[r["key"] for r in subset], est_col].sum()
        input_tokens = sum(r["tokens"]["cached"] + r["tokens"]["input"] for r in subset)
        output_tokens = sum(r["tokens"]["reasoning"] + r["tokens"]["output"] for r in subset)
        correct = sum(1 for r in subset
                      if r["record"] and truth[r["key"]] and r["record"]["primary_cause"] == truth[r["key"]])
        lenient = sum(1 for r in subset if r["record"] and truth[r["key"]]
                      and truth[r["key"]] in [r["record"]["primary_cause"], r["record"]["secondary_cause"]])
        scored = sum(1 for r in subset if truth[r["key"]])
        rows.append({"judge": judge, "condition": condition, "n": len(subset),
                     "strict": f"{correct}/{scored}", "lenient": f"{lenient}/{scored}",
                     "input_ratio": round(input_tokens / est, 2),
                     "out_per_call": round(output_tokens / len(subset)),
                     "cost": round(sum(r["cost"] for r in subset), 2)})
report = pd.DataFrame(rows)
print(report.to_string(index=False))

# Full-sweep forecast: measured input ratio x all-242 est tokens + per-call output average x 484
print("\nFull-sweep forecast (242 episodes x 2 conditions per judge):")
total = 0.0
for judge in JUDGES:
    in_price, out_price = PRICES[judge]
    ratio = report[report.judge == judge].input_ratio.mean()
    out_avg = report[report.judge == judge].out_per_call.mean()
    est_input = (sizes.pure_est_tokens.sum() + sizes.feedback_est_tokens.sum()) * ratio
    prompt_overhead = 484 * 1200  # instruction head+tail ~3.9k chars / 3.25
    cost = (est_input + prompt_overhead) / 1e6 * in_price + 484 * out_avg / 1e6 * out_price
    total += cost
    print(f"  {judge}: input ~{(est_input + prompt_overhead) / 1e6:.1f}M x ${in_price} "
          f"+ output ~{484 * out_avg / 1e6:.2f}M x ${out_price} = ${cost:.0f}")
print(f"  TOTAL ~${total:.0f} (checkpoint spend already covers {len(records)} of the 1,452 calls)")
