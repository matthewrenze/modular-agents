# Scratch: summarize agentic-judge (E1) records — retrieval strategy, sizes, and accuracy vs the
# C2 ensemble ground truth (majority of the three labelers, decisions section 81).
import json
import glob
import os
from collections import Counter

LABELER_FOLDER = "../data/interp/diagnosis/labeler"
LABELERS = ["gpt-5.6-sol", "claude-fable-5", "gemini-3.1-pro-preview"]
AGENTIC_FOLDER = "../data/interp/diagnosis/agentic-judge"

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

for judge in sorted(os.listdir(AGENTIC_FOLDER)):
    paths = sorted(glob.glob(f"{AGENTIC_FOLDER}/{judge}/*.json"))
    if not paths:
        continue
    print(f"\n=== {judge} ({len(paths)} records) ===")
    correct, scored, total_cost = 0, 0, 0.0
    for path in paths:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        key = os.path.splitext(os.path.basename(path))[0]
        truth = ground_truth(key)
        cause = data["record"]["primary_cause"] if data["record"] else data["outcome"].upper()
        match = "?" if truth is None else ("Y" if cause == truth else "N")
        if truth is not None:
            scored += 1
            correct += (cause == truth)
        total_cost += data["cost"]
        calls = ", ".join(f"{c['tool']}[{c['from']}-{c['to']}]" for c in data["retrieval"]["calls"])
        print(f"{data['agent_name']:13s} ep{data['episode']:>4} | {cause:26s} gt={truth or 'none':26s} {match} "
              f"| step={data['record']['root_cause_step'] if data['record'] else '-'} "
              f"| {data['read_turns']} turns, {data['retrieval']['total_chars']:>7} chars, ${data['cost']:.3f}")
        print(f"              calls: {calls}")
    print(f"accuracy vs GT: {correct}/{scored}; total cost ${total_cost:.2f}")
