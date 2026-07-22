# Scratch: list residual malformed agentic-judge records per judge (post re-run).
import json
import glob
import os

AGENTIC_FOLDER = "../data/interp/diagnosis/agentic-judge"
JUDGES = ["gpt-5.6-sol", "claude-fable-5", "gemini-3.1-pro-preview"]

for judge in JUDGES:
    paths = sorted(glob.glob(f"{AGENTIC_FOLDER}/{judge}/*.json"))
    malformed = []
    for path in paths:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if data["outcome"] == "malformed":
            key = os.path.splitext(os.path.basename(path))[0]
            malformed.append(key)
    print(f"{judge}: {len(paths)} records, {len(malformed)} malformed")
    for key in malformed:
        print(f"  {key}")
