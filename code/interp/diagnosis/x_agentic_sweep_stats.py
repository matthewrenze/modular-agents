# Scratch: compact full-grid summary of the agentic-judge (E1) sweep — accuracy vs the C2
# ensemble ground truth, retrieval/token/cost totals, malformed rates. Formal stats = task 4.3.
import json
import glob
import os
from collections import Counter, defaultdict

LABELER_FOLDER = "../data/interp/diagnosis/labeler"
LABELERS = ["gpt-5.6-sol", "claude-fable-5", "gemini-3.1-pro-preview"]
AGENTIC_FOLDER = "../data/interp/diagnosis/agentic-judge"
JUDGES = ["gpt-5.6-sol", "claude-fable-5", "gemini-3.1-pro-preview"]

def ground_truth(key):
    votes = []
    for labeler in LABELERS:
        path = f"{LABELER_FOLDER}/{labeler}/{key}.json"
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                record = json.load(f)["record"]
            if record:
                votes.append(record["primary_cause"])
    counts = Counter(votes)
    slug, count = counts.most_common(1)[0]
    return slug if count >= 2 else None

records = defaultdict(dict)  # key -> judge -> data
for judge in JUDGES:
    for path in sorted(glob.glob(f"{AGENTIC_FOLDER}/{judge}/*.json")):
        key = os.path.splitext(os.path.basename(path))[0]
        with open(path, "r", encoding="utf-8") as f:
            records[key][judge] = json.load(f)

truths = {key: ground_truth(key) for key in records}
arch_of = {key: ("modular" if "--modular-full--" in key else "react") for key in records}

print("=== per judge x architecture ===")
grand_cost = 0.0
for judge in JUDGES:
    for arch in ["modular", "react"]:
        keys = [k for k in records if arch_of[k] == arch and judge in records[k]]
        datas = [records[k][judge] for k in keys]
        mal = sum(1 for d in datas if d["outcome"] == "malformed")
        valid = [(k, d) for k, d in zip(keys, datas) if d["record"] is not None and truths[k]]
        correct = sum(1 for k, d in valid if d["record"]["primary_cause"] == truths[k])
        chars = [d["retrieval"]["total_chars"] for d in datas]
        turns = [d["read_turns"] for d in datas]
        in_tok = [d["tokens"]["cached"] + d["tokens"]["input"] for d in datas]
        cost = sum(d["cost"] for d in datas)
        grand_cost += cost
        n = len(datas)
        print(f"{judge:24s} {arch:7s} n={n:3d} malformed={mal:2d} ({mal/max(n,1):.0%}) "
              f"| acc(valid)={correct}/{len(valid)}={correct/max(len(valid),1):.3f} "
              f"| acc(all)={correct}/{n}={correct/max(n,1):.3f} "
              f"| retrieved chars mean={sum(chars)/max(n,1):,.0f} | turns mean={sum(turns)/max(n,1):.1f} "
              f"| input tok mean={sum(in_tok)/max(n,1):,.0f} | cost=${cost:.2f}")

print("\n=== pooled + majority vote per architecture ===")
for arch in ["modular", "react"]:
    keys = [k for k in records if arch_of[k] == arch and truths[k]]
    pooled_n = pooled_c = 0
    maj_c = maj_novote = 0
    for k in keys:
        votes = []
        for judge in JUDGES:
            d = records[k].get(judge)
            if d and d["record"]:
                pooled_n += 1
                pooled_c += (d["record"]["primary_cause"] == truths[k])
                votes.append(d["record"]["primary_cause"])
        top = Counter(votes).most_common(1)
        if top and top[0][1] >= 2:
            maj_c += (top[0][0] == truths[k])
        else:
            maj_novote += 1
    print(f"{arch:7s} pooled strict {pooled_c}/{pooled_n} = {pooled_c/max(pooled_n,1):.3f} "
          f"| majority-vote {maj_c}/{len(keys)} = {maj_c/max(len(keys),1):.3f} (no-vote {maj_novote})")

print("\n=== retrieval chars per architecture (valid + malformed, all judges) ===")
for arch in ["modular", "react"]:
    chars = [d["retrieval"]["total_chars"] for k in records if arch_of[k] == arch
             for d in records[k].values()]
    chars.sort()
    n = len(chars)
    print(f"{arch:7s} n={n} mean={sum(chars)/max(n,1):,.0f} median={chars[n//2]:,} "
          f"p90={chars[int(n*0.9)]:,} max={chars[-1]:,}")

print("\n=== per-class pooled accuracy (classes with >= 5 GT episodes) ===")
by_class = defaultdict(lambda: [0, 0])
for k in records:
    if not truths[k]:
        continue
    for judge in JUDGES:
        d = records[k].get(judge)
        if d and d["record"]:
            by_class[truths[k]][1] += 1
            by_class[truths[k]][0] += (d["record"]["primary_cause"] == truths[k])
for slug, (c, n) in sorted(by_class.items(), key=lambda x: -x[1][1]):
    if n >= 15:
        print(f"{slug:32s} {c:3d}/{n:3d} = {c/n:.3f}")

print(f"\ngrand total cost ${grand_cost:.2f}")
print(f"episodes with all 3 judges: {sum(1 for k in records if len(records[k]) == 3)}/242")
