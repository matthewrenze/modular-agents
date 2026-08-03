# k-sweep wave status one-liner. Run in WSL: python3 x_wave_status.py
# Prints: n/total (%) | success, fail, error (%-success) | cost | ETA
# Edit ARMS/BASE per wave (BASE = baseline arm used for per-eval ETA priors).
import csv, glob, os
from collections import defaultdict

ROOT = "/mnt/c/Users/Matthew/Dropbox/Professional/Research/Projects/Modular Agents/Repositories/modular-agents-kn/data/artifacts/v6.0/test/gpt-5.4"
ARMS = ["modular-kn"]
BASE = {"modular-kn": "modular-full"}
EVALS = ["tw-simple-1", "tw-treasure-1", "tw-treasure-2", "tw-treasure-3",
         "tw-coin-1", "tw-coin-2", "tw-coin-3",
         "tw-cooking-1", "tw-cooking-2", "tw-cooking-3"]

def read_rows(agent, ev):
    rows = []
    for p in glob.glob(os.path.join(ROOT, agent, ev, "*results.csv")):
        with open(p, newline="", encoding="utf-8") as f:
            rows.extend(list(csv.DictReader(f)))
    return rows

base_time = {}
for arm in ARMS:
    for ev in EVALS:
        rows = read_rows(BASE[arm], ev)
        if rows:
            base_time[(arm, ev)] = sum(float(r["total_time"]) for r in rows) / len(rows)

done = succ = fail = err = 0
cost = 0.0
eta_s = 0.0
per_arm = defaultdict(lambda: [0, 0])
for arm in ARMS:
    for ev in EVALS:
        rows = read_rows(arm, ev)
        n = len(rows)
        done += n
        per_arm[arm][0] += n
        per_arm[arm][1] += 10
        e = sum(1 for r in rows if r["error"].strip())
        s = sum(1 for r in rows if r["success"] == "True")
        err += e
        succ += s
        fail += n - s - e
        cost += sum(float(r["total_cost"]) for r in rows)
        remaining = 10 - n
        if remaining > 0:
            if n > 0:
                per_ep = sum(float(r["total_time"]) for r in rows) / n
            else:
                per_ep = base_time.get((arm, ev), 300) * (1.25 if arm.startswith("modular") else 1.1)
            eta_s = max(eta_s, remaining * per_ep)

total = 100 * len(ARMS)
pct = 100.0 * done / total
succ_pct = 100.0 * succ / done if done else 0.0
arm_bits = " | ".join(f"{a} {per_arm[a][0]}/{per_arm[a][1]}" for a in ARMS)
print(f"{done}/{total} ({pct:.0f}%) | {succ} success, {fail} fail, {err} error ({succ_pct:.0f}% success) | ${cost:.2f} | ETA ~{eta_s / 60:.0f} min")
print(f"per-arm: {arm_bits}")
